const readUvLock = require("./readUvLock");
const checkCompliance = require("./complianceCheck");

const data = readUvLock();
const packages = data.package || [];

const violations = checkCompliance(packages);

if (violations.length === 0) {
    console.log("✅ JavaScript compliance passed");
    process.exit(0);
} else {
    console.log("❌ JavaScript compliance failed");
    violations.forEach(v => console.log("-", v));
    process.exit(1);
}
