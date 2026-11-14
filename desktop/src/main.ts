import { spawn, type ChildProcess } from "node:child_process";
import { cpSync, existsSync, mkdirSync, readdirSync } from "node:fs";
import net from "node:net";
import path from "node:path";
import {
  app,
  BrowserWindow,
  dialog,
  Menu,
  shell,
} from "electron";

const PROJECT_ROOT = path.resolve(__dirname, "..", "..");
app.setName("Shop Management System");

const DATA_DIRECTORY = path.join(
  app.isPackaged ? app.getPath("userData") : PROJECT_ROOT,
  "storage",
);

let backend: ChildProcess | undefined;
let backendUrl: string | undefined;
let isQuitting = false;
let startupError: Error | undefined;

function prepareDataDirectory(): void {
  if (!app.isPackaged) {
    mkdirSync(DATA_DIRECTORY, { recursive: true });
    return;
  }

  const legacyDirectory = path.join(path.dirname(app.getPath("exe")), "storage");
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

function startBackend(port: number): ChildProcess {
  const environment = {
    ...process.env,
    SHOPMANAGER_DATA_DIR: DATA_DIRECTORY,
    SHOPMANAGER_DESKTOP: "1",
    SHOPMANAGER_HOST: "127.0.0.1",
    SHOPMANAGER_PORT: String(port),
    SHOPMANAGER_DEBUG: "0",
  };

  if (app.isPackaged) {
    const executable = process.platform === "win32"
      ? "ShopManagementBackend.exe"
      : "ShopManagementBackend";
    const backendPath = path.join(
      process.resourcesPath,
      "backend",
      "ShopManagementBackend",
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
        "Shop Management System stopped",
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
              "https://github.com/info-fusion-tech-lab/ShopManagementSystem/releases/latest",
            );
          },
        },
      ],
    },
  ]));
}

function createWindow(url: string): void {
  const window = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 960,
    minHeight: 640,
    title: "Shop Management System",
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

app.whenReady().then(async () => {
  try {
    prepareDataDirectory();
    installApplicationMenu();
    const port = await getAvailablePort();
    const url = `http://127.0.0.1:${port}`;
    const processHandle = startBackend(port);
    await waitForBackend(url, processHandle);
    backendUrl = url;
    createWindow(url);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    dialog.showErrorBox("Could not start Shop Management System", message);
    app.quit();
  }
});

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
