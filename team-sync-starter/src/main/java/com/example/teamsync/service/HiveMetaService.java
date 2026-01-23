package com.example.teamsync.service;

import com.example.teamsync.util.ConfigService;
import org.apache.hadoop.hive.conf.HiveConf;
import org.apache.hadoop.hive.metastore.IMetaStoreClient;
import org.apache.hadoop.hive.metastore.HiveMetaStoreClient;

import java.util.List;

public class HiveMetaService {
    private final ConfigService.AppConfig config;
    private final KerberosAuth kerberos;

    public HiveMetaService(ConfigService.AppConfig config, KerberosAuth kerberos) {
        this.config = config;
        this.kerberos = kerberos;
    }

    public List<String> listDatabases() {
        var hc = new HiveConf();
        hc.setVar(HiveConf.ConfVars.METASTOREURIS, config.hms().uris());
        hc.setBoolVar(HiveConf.ConfVars.METASTORE_USE_THRIFT_SASL, config.hms().useKerberos());
        if (config.hms().useKerberos()) {
            hc.set("hive.metastore.sasl.enabled", "true");
            hc.set("hive.metastore.kerberos.principal", config.hms().principal());
            return kerberos.doAsTicketCache(() -> {
                try (IMetaStoreClient client = new HiveMetaStoreClient(hc)) {
                    return client.getAllDatabases();
                }
            });
        } else {
            try (IMetaStoreClient client = new HiveMetaStoreClient(hc)) {
                return client.getAllDatabases();
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        }
    }
}
