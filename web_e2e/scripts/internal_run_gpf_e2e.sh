#!/bin/bash

set -e

echo "E2E                       : ${E2E}"
echo "CONTAINER_GPF_DEV         : ${CONTAINER_GPF_DEV}"

cd ${E2E}

rm -rf node_modules package-lock.json
npm install


${WD}/scripts/wait-for-it.sh ${CONTAINER_GPF_DEV}:9001 --timeout=360
${WD}/scripts/wait-for-it.sh ${CONTAINER_GPF_DEV}:80 --timeout=360


# ng e2e --baseUrl http://${CONTAINER_GPF_DEV}/gpf/
./node_modules/.bin/cypress run --browser chrome --config baseUrl=http://${CONTAINER_GPF_DEV}/gpf/ --spec cypress/integration/user-management-spec.ts, cypress/integration/app-spec.ts, cypress/integration/gene-weights-spec.ts, cypress/integration/share-query-spec.ts, cypress/integration/save-query-spec.ts, cypress/integration/datasets-spec.ts, cypress/integration/enrichment-tool-spec.ts, cypress/integration/genotype-browser-spec.ts
