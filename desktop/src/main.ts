import { spawn, type ChildProcess } from "node:child_process";
import {
  cpSync,
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  writeFileSync,
} from "node:fs";
import { randomBytes } from "node:crypto";
import net from "node:net";
import path from "node:path";
import {
  app,
  BrowserWindow,
  dialog,
  Menu,
  safeStorage,
  shell,
} from "electron";

const PROJECT_ROOT = path.resolve(__dirname, "..", "..");
app.setName("DukaanDesk");
app.setPath(
  "userData",
  path.join(app.getPath("appData"), "Shop Management System"),
);
const hasSingleInstanceLock = app.requestSingleInstanceLock();
if (!hasSingleInstanceLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    const [window] = BrowserWindow.getAllWindows();
    if (window) {
      if (window.isMinimized()) {
        window.restore();
      }
      window.focus();
    }
  });
}

const DATA_DIRECTORY = path.join(app.getPath("userData"), "storage");
const ENCRYPTION_KEY_FILE = path.join(
  app.getPath("userData"),
  "encryption-key.dat",
);

let backend: ChildProcess | undefined;
let backendUrl: string | undefined;
let isQuitting = false;
let startupError: Error | undefined;

function prepareDataDirectory(): void {
  const legacyDirectory = app.isPackaged
    ? path.join(path.dirname(app.getPath("exe")), "storage")
    : path.join(PROJECT_ROOT, "storage");
  if (
    existsSync(legacyDirectory)
    && (!existsSync(DATA_DIRECTORY) || readdirSync(DATA_DIRECTORY).length === 0)
  ) {
    mkdirSync(DATA_DIRECTORY, { recursive: true });
    cpSync(legacyDirectory, DATA_DIRECTORY, { recursive: true, force: false });
  } else {
    mkdirSync(DATA_DIRECTORY, { recursive: true });
  }
}

function getEncryptionKey(): string {
  if (!safeStorage.isEncryptionAvailable()) {
    throw new Error("Secure operating-system storage is unavailable.");
  }
  if (
    process.platform === "linux"
    && safeStorage.getSelectedStorageBackend() === "basic_text"
  ) {
    throw new Error(
      "Configure a Linux desktop keyring (Secret Service or KWallet) to encrypt shop data.",
    );
  }

  if (existsSync(ENCRYPTION_KEY_FILE)) {
    try {
      const key = safeStorage.decryptString(readFileSync(ENCRYPTION_KEY_FILE));
      if (!/^[A-Za-z0-9_-]{43}=$/.test(key)) {
        throw new Error("The stored encryption key has an invalid format.");
      }
      return key;
    } catch (error) {
      throw new Error(
        `Could not unlock the local encryption key: ${String(error)}`,
      );
    }
  }

  const profileDirectory = path.join(DATA_DIRECTORY, "Profiles");
  if (
    existsSync(path.join(DATA_DIRECTORY, "Accounts.json"))
    || (existsSync(profileDirectory) && readdirSync(profileDirectory).length > 0)
  ) {
    throw new Error(
      "The encryption key is missing while encrypted shop data exists. Restore the original key from backup.",
    );
  }

  const key = randomBytes(32)
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
  mkdirSync(path.dirname(ENCRYPTION_KEY_FILE), { recursive: true });
  writeFileSync(
    ENCRYPTION_KEY_FILE,
    safeStorage.encryptString(key),
    { mode: 0o600 },
  );
  return key;
}

function getAvailablePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      if (!address || typeof address === "string") {
        server.close();
        reject(new Error("Could not allocate a local application port."));
        return;
      }

      server.close((error) => {
        if (error) {
          reject(error);
        } else {
          resolve(address.port);
        }
      });
    });
  });
}

function startBackend(port: number, encryptionKey: string): ChildProcess {
  const environment = {
    ...process.env,
    SHOPMANAGER_DATA_DIR: DATA_DIRECTORY,
    SHOPMANAGER_DESKTOP: "1",
    SHOPMANAGER_ENCRYPTION_KEY: encryptionKey,
    SHOPMANAGER_HOST: "127.0.0.1",
    SHOPMANAGER_PORT: String(port),
    SHOPMANAGER_DEBUG: "0",
  };

  if (app.isPackaged) {
    const executable = process.platform === "win32"
      ? "DukaanDeskBackend.exe"
      : "DukaanDeskBackend";
    const backendPath = path.join(
      process.resourcesPath,
      "backend",
      "DukaanDeskBackend",
      executable,
    );
    backend = spawn(backendPath, [], {
      cwd: DATA_DIRECTORY,
      env: environment,
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });
  } else {
    const python = process.env.SHOPMANAGER_PYTHON
      || (process.platform === "win32" ? "python" : "python3");
    backend = spawn(python, [path.join(PROJECT_ROOT, "app.py")], {
      cwd: PROJECT_ROOT,
      env: environment,
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });
  }

  backend.once("error", (error) => {
    startupError = error;
  });
  backend.stdout?.on("data", (chunk: Buffer) => {
    console.log(`[backend] ${chunk.toString().trimEnd()}`);
  });
  backend.stderr?.on("data", (chunk: Buffer) => {
    console.error(`[backend] ${chunk.toString().trimEnd()}`);
  });
  backend.once("exit", (code, signal) => {
    if (!isQuitting && BrowserWindow.getAllWindows().length > 0) {
      const reason = signal ? `signal ${signal}` : `exit code ${code}`;
      dialog.showErrorBox(
        "DukaanDesk stopped",
        `The local application service stopped unexpectedly (${reason}).`,
      );
      app.quit();
    }
  });

  return backend;
}

async function waitForBackend(url: string, processHandle: ChildProcess): Promise<void> {
  const deadline = Date.now() + 30_000;
  let lastError: unknown;

  while (Date.now() < deadline) {
    if (startupError) {
      throw startupError;
    }
    if (processHandle.exitCode !== null) {
      throw new Error(`The local service exited with code ${processHandle.exitCode}.`);
    }

    try {
      const response = await fetch(`${url}/health`, {
        signal: AbortSignal.timeout(1_000),
      });
      if (response.ok) {
        return;
      }
      lastError = new Error(`Health check returned HTTP ${response.status}.`);
    } catch (error) {
      lastError = error;
    }

    await new Promise((resolve) => setTimeout(resolve, 250));
  }

  throw new Error(
    `The local service did not become ready within 30 seconds. ${String(lastError ?? "")}`,
  );
}

function installApplicationMenu(): void {
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    {
      label: "File",
      submenu: [
        {
          label: "Open Data Folder",
          click: () => {
            void shell.openPath(DATA_DIRECTORY).then((error) => {
              if (error) {
                dialog.showErrorBox("Could not open data folder", error);
              }
            });
          },
        },
        { type: "separator" },
        { role: "quit" },
      ],
    },
    {
      label: "Help",
      submenu: [
        {
          label: "Download and product information",
          click: () => {
            void shell.openExternal(
              "https://github.com/info-fusion-tech-lab/DukaanDesk/releases/latest",
            );
          },
        },
      ],
    },
  ]));
}

function createWindow(url: string): void {
  const iconPath = app.isPackaged
    ? path.join(process.resourcesPath, "app-icon.ico")
    : path.join(PROJECT_ROOT, "store.ico");
  const window = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 960,
    minHeight: 640,
    title: "DukaanDesk",
    icon: iconPath,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  void window.loadURL(url);
}

app.on("before-quit", () => {
  isQuitting = true;
  backend?.kill();
});

if (hasSingleInstanceLock) {
  app.whenReady().then(async () => {
    try {
      prepareDataDirectory();
      installApplicationMenu();
      const encryptionKey = getEncryptionKey();
      const port = await getAvailablePort();
      const url = `http://127.0.0.1:${port}`;
      const processHandle = startBackend(port, encryptionKey);
      await waitForBackend(url, processHandle);
      backendUrl = url;
      createWindow(url);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      dialog.showErrorBox("Could not start DukaanDesk", message);
      app.quit();
    }
  });
}

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0 && backendUrl) {
    createWindow(backendUrl);
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
