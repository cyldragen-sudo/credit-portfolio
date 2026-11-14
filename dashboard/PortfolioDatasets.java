import java.nio.file.*;
import java.util.*;
import java.sql.*;
import com.fr.json.*;
import com.fr.base.Parameter;
import com.fr.data.impl.*;
import com.fr.stable.xml.XMLPrintWriter;

/** Serialize native datasets; only private local output contains protected credentials. */
public class PortfolioDatasets {
  public static void main(String[] args) throws Exception {
    Path root=Paths.get(args[0]);
    boolean local=args.length>1 && args[1].equals("local");
    com.fr.security.encryption.storage.StorageEncryptionManager.getInstance().init();
    JSONArray definitions=new JSONArray(Files.readString(root.resolve("dashboard/datasets.json")));
    JSONArray metadata=new JSONArray();
    JDBCDatabaseConnection jdbc=null;
    if(local) {
      String[] parts=Files.readString(root.resolve(".private/reader.pgpass")).strip().split(":",5);
      jdbc=new JDBCDatabaseConnection();
      jdbc.setDriver("org.postgresql.Driver");
      jdbc.setURL("jdbc:postgresql://127.0.0.1:55433/credit_portfolio_demo?ApplicationName=Credit_Portfolio_FineReport&connectTimeout=8&socketTimeout=25");
      jdbc.setUser("credit_report_user");jdbc.setPassword(parts[4]);jdbc.setSchema("credit");
      com.fr.data.pool.DBCPConnectionPoolAttr pool=new com.fr.data.pool.DBCPConnectionPoolAttr();
      pool.setInitialSize(0);pool.setMinIdle(0);pool.setMaxIdle(0);pool.setMaxActive(1);
      pool.setKeepAlive(false);pool.setTimeBetweenEvictionRunsMillis(1000);
      pool.setMinEvictableIdleTimeMillis(5000);pool.setMaxEvictableIdleTimeMillis(10000L);
      pool.setMaxWait(20000);pool.setTestOnBorrow(true);pool.setValidationQuery("SELECT 1");
      jdbc.setDbcpAttr(pool);
      Class.forName("org.postgresql.Driver");
    }
    Path target=root.resolve(local?".private/datasets.xml":"dashboard/datasets.xml");
    try(java.io.OutputStream out=Files.newOutputStream(target)) {
      XMLPrintWriter writer=XMLPrintWriter.create(out);writer.startTAG("TableDataMap");
      for(int index=0;index<definitions.length();index++) {
        JSONObject definition=definitions.getJSONObject(index);
        String sql=Files.readString(root.resolve(definition.getString("file")));
        JSONObject defaults=definition.getJSONObject("parameters");
        List<Parameter> parameters=new ArrayList<>();
        String expanded=sql;
        for(Map.Entry<String,Object> item:defaults) {
          int value=((Number)item.getValue()).intValue();
          parameters.add(new Parameter(item.getKey(),value));
          expanded=expanded.replace("$"+"{INT("+item.getKey()+")}",String.valueOf(value));
        }
        if(expanded.contains("$"+"{"))throw new IllegalArgumentException("Unexpanded parameter");
        DBTableData data=new DBTableData();data.setQuery(sql);
        data.setParameters(parameters.toArray(new Parameter[0]));
        data.setDatabase(local?jdbc:new NameDatabaseConnection("CREDIT_PORTFOLIO"));
        data.setMaxMemRowCount(-1);
        writer.startTAG("TableData").attr("name",definition.getString("name")).attr("class","com.fr.data.impl.DBTableData");
        data.writeXML(writer);writer.end();
        if(local) {
          try(java.sql.Connection c=DriverManager.getConnection(jdbc.getURL(),jdbc.getUser(),jdbc.getPassword());
              Statement statement=c.createStatement();ResultSet rows=statement.executeQuery(expanded)) {
            JSONArray columns=new JSONArray();
            for(int col=1;col<=rows.getMetaData().getColumnCount();col++)columns.put(rows.getMetaData().getColumnLabel(col));
            int count=0;while(rows.next())count++;
            JSONObject item=new JSONObject();item.put("name",definition.getString("name"));
            item.put("columns",columns);item.put("rows",count);metadata.put(item);
            System.out.println(definition.getString("name")+": "+count+" rows; read-only JDBC verified");
          }
        }
      }
      writer.end();writer.flush();
    }
    if(local) {
      Files.setPosixFilePermissions(target,java.nio.file.attribute.PosixFilePermissions.fromString("rw-------"));
      Files.writeString(root.resolve("validation/native-datasets.json"),metadata.toString());
    }
    System.out.println("Native dataset serialization complete: "+(local?"private local":"portable named connection"));
    try(java.io.OutputStream out=Files.newOutputStream(root.resolve("build/default-line.xml"))) {
      XMLPrintWriter writer=XMLPrintWriter.create(out);
      com.fr.plugin.chart.line.VanChartLinePlot plot=new com.fr.plugin.chart.line.VanChartLinePlot();
      plot.getyAxis().setCustomMinValue(true);
      plot.getyAxis().setMinValue(new com.fr.base.Formula("=0"));
      writer.startTAG("Plot").attr("class",plot.getClass().getName());plot.writeXML(writer);writer.end();writer.flush();
    }
    try(java.io.OutputStream out=Files.newOutputStream(root.resolve("build/default-funnel.xml"))) {
      XMLPrintWriter writer=XMLPrintWriter.create(out);
      com.fr.plugin.chart.funnel.VanChartFunnelPlot plot=new com.fr.plugin.chart.funnel.VanChartFunnelPlot();
      plot.setSort(false);
      writer.startTAG("Plot").attr("class",plot.getClass().getName());plot.writeXML(writer);writer.end();writer.flush();
    }
  }
}
