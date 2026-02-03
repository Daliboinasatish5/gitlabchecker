const fs = require("fs");
const toml = require("@iarna/toml");

function readUvLock() {
    const content = fs.readFileSync("uv.lock", "utf-8");
    return toml.parse(content);
}

module.exports = readUvLock;
