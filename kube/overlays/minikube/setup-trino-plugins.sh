kubectl cp trino-ai-443 trino-worker-0:/tmp/trino-ai-443
mv trino-ai-443 trino-ai
cp -r trino-ai /usr/lib/trino/plugin/

kubectl cp trino-trino-443 trino-worker-0:/tmp/trino-trino-443
mv trino-trino-443 trino-trino
cp -r trino-trino /usr/lib/trino/plugin/