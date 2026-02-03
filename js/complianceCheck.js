const rules = require("./rules");

function checkCompliance(packages) {
    const violations = [];

    for (const pkg of packages) {
        if (
            pkg.source &&
            !pkg.source.includes(rules.allowedRegistry)
        ) {
            violations.push(`Invalid registry: ${pkg.name}`);
        }
    }

    return violations;
}

module.exports = checkCompliance;
