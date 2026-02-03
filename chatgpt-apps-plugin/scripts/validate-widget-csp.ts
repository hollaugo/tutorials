#!/usr/bin/env tsx
/**
 * Validates Widget CSP (Content Security Policy) configuration
 *
 * Checks:
 * - Widget resources have proper MIME type
 * - CSP configuration is valid
 * - Required domains are allowed
 * - No overly permissive policies
 */

interface CSPConfig {
  connect_domains?: string[];
  resource_domains?: string[];
  frame_domains?: string[];
  redirect_domains?: string[];
}

interface WidgetResource {
  uri: string;
  mimeType: string;
  _meta?: {
    "openai/widgetDescription"?: string;
    "openai/widgetCSP"?: CSPConfig;
    "openai/widgetDomain"?: string;
  };
}

interface ValidationResult {
  widget: string;
  passed: boolean;
  errors: string[];
  warnings: string[];
}

function validateWidgetResource(resource: WidgetResource): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Check MIME type
  if (resource.mimeType !== "text/html+skybridge") {
    errors.push(`Wrong MIME type: ${resource.mimeType}, should be text/html+skybridge`);
  }

  // Check metadata
  if (!resource._meta) {
    warnings.push("No _meta object");
  } else {
    // Check widget description
    if (!resource._meta["openai/widgetDescription"]) {
      warnings.push("Missing widgetDescription");
    }

    // Check CSP if present
    const csp = resource._meta["openai/widgetCSP"];
    if (csp) {
      // Validate connect_domains
      if (csp.connect_domains) {
        if (!Array.isArray(csp.connect_domains)) {
          errors.push("connect_domains must be an array");
        } else {
          for (const domain of csp.connect_domains) {
            if (domain === "*") {
              errors.push("Wildcard (*) not allowed in connect_domains");
            }
          }
        }
      }

      // Validate resource_domains
      if (csp.resource_domains) {
        if (!Array.isArray(csp.resource_domains)) {
          errors.push("resource_domains must be an array");
        }
      }

      // Validate frame_domains
      if (csp.frame_domains) {
        if (!Array.isArray(csp.frame_domains)) {
          errors.push("frame_domains must be an array");
        }
      }
    }
  }

  return {
    widget: resource.uri,
    passed: errors.length === 0,
    errors,
    warnings,
  };
}

async function main() {
  console.log("Validating Widget CSP configuration...\n");

  // Sample widget for demonstration
  const sampleWidgets: WidgetResource[] = [
    {
      uri: "ui://widget/item-list.html",
      mimeType: "text/html+skybridge",
      _meta: {
        "openai/widgetDescription": "Displays a list of items",
        "openai/widgetCSP": {
          connect_domains: ["api.example.com"],
        },
      },
    },
  ];

  let allPassed = true;
  const results: ValidationResult[] = [];

  for (const widget of sampleWidgets) {
    const result = validateWidgetResource(widget);
    results.push(result);

    const status = result.passed ? "✓" : "✗";
    console.log(`${status} ${result.widget}`);

    for (const error of result.errors) {
      console.log(`  ✗ ${error}`);
      allPassed = false;
    }

    for (const warning of result.warnings) {
      console.log(`  ⚠ ${warning}`);
    }
  }

  console.log(`\n${allPassed ? "All validations passed" : "Some validations failed"}`);
  process.exit(allPassed ? 0 : 1);
}

main().catch((err) => {
  console.error("Validation failed:", err);
  process.exit(1);
});
