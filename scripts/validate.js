const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const BASE_DIR = path.join(__dirname, '..');
const REGISTRY_FILE = path.join(BASE_DIR, 'registry', 'datasets.json');
const SCHEMAS_DIR = path.join(BASE_DIR, 'schemas');
const CONTENT_DIR = path.join(BASE_DIR, 'content');
const OTA_DIR = path.join(BASE_DIR, 'ota');
const SEARCH_DIR = path.join(BASE_DIR, 'search');
const ASSETS_MANIFEST_FILE = path.join(BASE_DIR, 'media', 'assets.json');

// Helper to log with styling
function logSuccess(msg) { console.log(`\x1b[32m✔ SUCCESS:\x1b[0m ${msg}`); }
function logError(msg) { console.error(`\x1b[31m✘ ERROR:\x1b[0m ${msg}`); }
function logInfo(msg) { console.log(`\x1b[34mℹ INFO:\x1b[0m ${msg}`); }

// Generate SHA-256 checksum
function getSHA256(filePath) {
  const fileBuffer = fs.readFileSync(filePath);
  const hashSum = crypto.createHash('sha256');
  hashSum.update(fileBuffer);
  return hashSum.digest('hex');
}

// Simple validator mimicking JSON Schema constraints
function validateDataset(datasetId, data, idPattern) {
  if (!data || typeof data !== 'object') {
    throw new Error(`Dataset is not a JSON object`);
  }

  // Metadata Validation
  const meta = data.metadata;
  if (!meta || typeof meta !== 'object') {
    throw new Error(`Missing 'metadata' object`);
  }

  const requiredMeta = ['dataset', 'version', 'generatedAt', 'language', 'region', 'verified', 'source'];
  for (const field of requiredMeta) {
    if (meta[field] === undefined) {
      throw new Error(`Metadata missing required field: '${field}'`);
    }
  }

  if (meta.dataset !== datasetId) {
    throw new Error(`Metadata field 'dataset' expected '${datasetId}', got '${meta.dataset}'`);
  }

  if (isNaN(Date.parse(meta.generatedAt))) {
    throw new Error(`Metadata 'generatedAt' has invalid date format: '${meta.generatedAt}'`);
  }

  // Items Validation
  const items = data.items;
  if (!Array.isArray(items)) {
    throw new Error(`'items' must be an array`);
  }

  const ids = new Set();
  const slugs = new Set();

  const requiredItemFields = [
    'id', 'slug', 'title', 'description', 'status', 'tags',
    'relationships', 'verified', 'source', 'sourceUrl',
    'createdAt', 'updatedAt', 'verifiedAt', 'version'
  ];

  const allowedStatuses = ['confirmed', 'official', 'community', 'coming_soon', 'deprecated'];

  for (let idx = 0; idx < items.length; idx++) {
    const item = items[idx];
    const indexStr = `items[${idx}]`;

    for (const field of requiredItemFields) {
      if (item[field] === undefined) {
        throw new Error(`${indexStr} is missing required field: '${field}'`);
      }
    }

    // Pattern checking on ID
    if (!idPattern.test(item.id)) {
      throw new Error(`${indexStr} ID '${item.id}' does not match pattern ${idPattern}`);
    }

    // Slug formatting
    if (!/^[a-z0-9-]+$/.test(item.slug)) {
      throw new Error(`${indexStr} slug '${item.slug}' must be lowercase alphanumeric with hyphens`);
    }

    // Check unique ID
    if (ids.has(item.id)) {
      throw new Error(`Duplicate ID found: '${item.id}'`);
    }
    ids.add(item.id);

    // Check unique Slug
    if (slugs.has(item.slug)) {
      throw new Error(`Duplicate Slug found: '${item.slug}'`);
    }
    slugs.add(item.slug);

    // Status Enum check
    if (!allowedStatuses.includes(item.status)) {
      throw new Error(`${indexStr} status '${item.status}' is invalid. Allowed: ${allowedStatuses.join(', ')}`);
    }

    // Dates checks
    if (isNaN(Date.parse(item.createdAt))) throw new Error(`${indexStr} invalid createdAt date: '${item.createdAt}'`);
    if (isNaN(Date.parse(item.updatedAt))) throw new Error(`${indexStr} invalid updatedAt date: '${item.updatedAt}'`);
    if (isNaN(Date.parse(item.verifiedAt))) throw new Error(`${indexStr} invalid verifiedAt date: '${item.verifiedAt}'`);

    // Relationships check
    if (item.relationships && typeof item.relationships !== 'object') {
      throw new Error(`${indexStr} relationships must be an object`);
    }
  }

  return { ids, items };
}

function runValidation() {
  logInfo("Starting ViceBase CDN validation pipeline...");

  try {
    // 1. Validate Registry File
    if (!fs.existsSync(REGISTRY_FILE)) {
      throw new Error(`Registry file not found at ${REGISTRY_FILE}`);
    }
    const registry = JSON.parse(fs.readFileSync(REGISTRY_FILE, 'utf8'));
    if (!Array.isArray(registry.datasets)) {
      throw new Error(`Registry datasets property must be an array`);
    }
    logSuccess("Registry datasets format verified.");

    const datasetMap = new Map();
    const allIds = new Set();
    const relationshipReferences = [];

    // 2. Validate schemas and load datasets
    for (const datasetInfo of registry.datasets) {
      if (!datasetInfo.enabled) {
        logInfo(`Skipping disabled dataset: ${datasetInfo.id}`);
        continue;
      }

      const schemaMap = {
        "locations": "location",
        "characters": "character",
        "vehicles": "vehicle",
        "weapons": "weapon",
        "timeline": "timeline",
        "news": "news"
      };
      const schemaName = schemaMap[datasetInfo.id] || datasetInfo.id;
      const schemaPath = path.join(SCHEMAS_DIR, `${schemaName}.schema.json`);
      const datasetPath = path.join(BASE_DIR, datasetInfo.path);

      if (!fs.existsSync(schemaPath)) {
        throw new Error(`Schema file not found for dataset ${datasetInfo.id} at ${schemaPath}`);
      }
      if (!fs.existsSync(datasetPath)) {
        throw new Error(`Dataset content file not found at ${datasetPath}`);
      }

      const rawContent = fs.readFileSync(datasetPath, 'utf8');
      const data = JSON.parse(rawContent);

      // Setup prefix check based on dataset ID
      const prefix = schemaName;
      const idPattern = new RegExp(`^${prefix}_[a-z0-9_]+$`);

      logInfo(`Validating dataset: ${datasetInfo.id}`);
      const { ids, items } = validateDataset(datasetInfo.id, data, idPattern);
      logSuccess(`Dataset '${datasetInfo.id}' successfully validated (${items.length} records).`);

      // Store IDs for referential integrity checks
      for (const id of ids) {
        allIds.add(id);
      }

      // Collect relationships for cross-dataset check
      for (const item of items) {
        if (item.relationships) {
          for (const relType in item.relationships) {
            const relArray = item.relationships[relType];
            if (Array.isArray(relArray)) {
              for (const refId of relArray) {
                relationshipReferences.push({
                  sourceId: item.id,
                  targetId: refId
                });
              }
            }
          }
        }
      }

      datasetMap.set(datasetInfo.id, {
        info: datasetInfo,
        items,
        path: datasetPath,
        checksum: getSHA256(datasetPath)
      });
    }

    // 3. Verify Referential Integrity
    logInfo("Checking relationship references...");
    for (const ref of relationshipReferences) {
      if (!allIds.has(ref.targetId)) {
        throw new Error(`Referential integrity error: item '${ref.sourceId}' references non-existent ID '${ref.targetId}'`);
      }
    }
    logSuccess("Referential integrity verified. All relationship IDs exist.");

    // 4. Validate Asset Manifest Match
    logInfo("Validating asset manifest items...");
    if (!fs.existsSync(ASSETS_MANIFEST_FILE)) {
      throw new Error(`Asset manifest file not found at ${ASSETS_MANIFEST_FILE}`);
    }
    const assetsManifest = JSON.parse(fs.readFileSync(ASSETS_MANIFEST_FILE, 'utf8'));
    if (!Array.isArray(assetsManifest.assets)) {
      throw new Error(`Asset manifest 'assets' must be an array`);
    }

    for (const asset of assetsManifest.assets) {
      if (!allIds.has(asset.id)) {
        throw new Error(`Asset manifest refers to ID '${asset.id}' which does not exist in any dataset.`);
      }
      // Check paths
      const absPath = path.join(BASE_DIR, asset.path);
      if (!fs.existsSync(absPath)) {
        throw new Error(`Asset directory path does not exist for '${asset.id}': ${asset.path}`);
      }
    }
    logSuccess("Asset manifest references validated successfully.");

    // 5. Generate search/index.json
    logInfo("Compiling Search Index (search/index.json)...");
    const searchIndex = [];
    for (const [datasetId, dataset] of datasetMap.entries()) {
      const typeName = datasetId.slice(0, -1); // e.g. characters -> character
      for (const item of dataset.items) {
        searchIndex.push({
          id: item.id,
          slug: item.slug,
          title: item.title,
          description: item.description,
          type: typeName,
          tags: item.tags,
          status: item.status
        });
      }
    }

    if (!fs.existsSync(SEARCH_DIR)) {
      fs.mkdirSync(SEARCH_DIR, { recursive: true });
    }
    fs.writeFileSync(
      path.join(SEARCH_DIR, 'index.json'),
      JSON.stringify(searchIndex, null, 2),
      'utf8'
    );
    logSuccess("Search index generated successfully.");

    // 6. Generate ota/manifest.json and ota/version.json
    logInfo("Building OTA Manifest and version files...");
    const latestGeneratedAt = new Date().toISOString();
    
    // Sort datasets topologically based on dependsOn to guarantee download order
    const sortedDatasetIds = [];
    const visited = new Set();
    const tempVisited = new Set();

    function visit(id) {
      if (tempVisited.has(id)) {
        throw new Error(`Circular dependency detected involving dataset '${id}'`);
      }
      if (!visited.has(id)) {
        tempVisited.add(id);
        const ds = datasetMap.get(id);
        if (ds && ds.info.dependsOn) {
          for (const dep of ds.info.dependsOn) {
            visit(dep);
          }
        }
        tempVisited.delete(id);
        visited.add(id);
        sortedDatasetIds.push(id);
      }
    }

    for (const datasetId of datasetMap.keys()) {
      visit(datasetId);
    }

    const manifestDatasets = sortedDatasetIds.map(id => {
      const ds = datasetMap.get(id);
      return {
        id: ds.info.id,
        version: ds.info.version,
        file: ds.info.path,
        checksum: ds.checksum,
        records: ds.items.length,
        dependsOn: ds.info.dependsOn
      };
    });

    const currentManifestVersion = "3.0.0"; // Semver version for CDN OTA manifest structure
    const manifest = {
      contentVersion: currentManifestVersion,
      generatedAt: latestGeneratedAt,
      minimumAppVersion: "1.0.0",
      datasets: manifestDatasets
    };

    if (!fs.existsSync(OTA_DIR)) {
      fs.mkdirSync(OTA_DIR, { recursive: true });
    }

    fs.writeFileSync(
      path.join(OTA_DIR, 'manifest.json'),
      JSON.stringify(manifest, null, 2),
      'utf8'
    );
    logSuccess("ota/manifest.json generated successfully.");

    const versionJson = {
      databaseVersion: currentManifestVersion,
      contentVersion: currentManifestVersion,
      appMinimumVersion: "1.0.0",
      lastUpdated: latestGeneratedAt
    };

    fs.writeFileSync(
      path.join(OTA_DIR, 'version.json'),
      JSON.stringify(versionJson, null, 2),
      'utf8'
    );
    logSuccess("ota/version.json generated successfully.");

    logSuccess("All validations completed. CDN Repository is fully OTA ready!");

  } catch (error) {
    logError(error.message);
    process.exit(1);
  }
}

runValidation();
