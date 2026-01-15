import { spawn } from "child_process";

console.log("Starting Python Flask App...");

// Spawn the python process and inherit stdio so logs show up
const pythonProcess = spawn("python3", ["main.py"], {
  stdio: "inherit",
});

pythonProcess.on("close", (code) => {
  console.log(`Python process exited with code ${code}`);
  process.exit(code ?? 0);
});
