import java.util.HashMap;

public class Main {
    private static boolean IS_DEBUG_MODE = false;
    
    public static void main(String[] args) {
        //
        // Parse CLI parameters
        //
        if (args.length >= 1 && args[0].equalsIgnoreCase("debug")) {
            IS_DEBUG_MODE = true;
        }
        
        //
        // SQL DBMS Settings
        //
        HashMap<String, String[]> sql_databases = new HashMap<>(); // Map of available SQL DBMSs and their settings
        String[] db_settings = new String[3]; // Array to temporarily store SQL DBMS settings

        String mysql_db_url = "jdbc:postgresql://" + System.getenv("POSTGRES_HOST") + ":5432/"; // DB Connection URL for PostgreSQL
        String db_driver = "org.postgresql.Driver";
        String db_username = "postgres";
        String db_password = System.getenv("POSTGRES_PASSWORD");

        db_settings[0] = db_driver;
        db_settings[1] = db_username;
        db_settings[2] = db_password;

        sql_databases.put(mysql_db_url, db_settings); // Add PostgreSQL as SQL DBMS

        // DataGenerator is used both for DDL and DML operations. It first creates tables.
        // Then loads sample data from csv files, and by using that data generates necessary SQL tables
        // and Neo4j nodes for the benchmark.
        DataGenerator dataGenerator = new DataGenerator(sql_databases, mysql_db_url);

        // Create tables for "warehouse" and "testdata" databases
        dataGenerator.createTables();
        dataGenerator.createSampleTables(mysql_db_url);
        // Insert sample data into "testdata" database.
        // This will be used for generating "warehouse" table records.
        dataGenerator.loadSampleData(1, mysql_db_url);

        // Generate benchmark records for "warehouse" database
        if (IS_DEBUG_MODE) {
            dataGenerator.insertItemsAndWorkTypes(1, 10, 10, 100);
            dataGenerator.insertWorkData(1, 1, 10, 10, 10);
            dataGenerator.insertCustomerData(1, 1, 10, 10, 0, 10, 10);
        } else {
            dataGenerator.insertItemsAndWorkTypes(10, 10, 10000, 10000);
            dataGenerator.insertWorkData(10, 1000, 10, 10, 10);
            dataGenerator.insertCustomerData(10, 1000, 10, 10, 0, 10, 10);
        }

        // Sequential Invoice Generation
//        HashMap<String, Integer> customerInvoice = dataGenerator.insertSequentialInvoices(1, 10, 100);
//
//        int invoiceIndex = customerInvoice.get("invoiceIndex");
//        int customerIndex = customerInvoice.get("customerIndex");
//
//        dataGenerator.cleanSequentialInvoices(customerIndex);
    }
}
