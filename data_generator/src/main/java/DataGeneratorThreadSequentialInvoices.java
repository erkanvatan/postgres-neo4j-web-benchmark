import java.sql.*;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.*;
import java.util.concurrent.locks.ReentrantLock;

public class DataGeneratorThreadSequentialInvoices extends Thread {

    private HashMap<String, String[]> sql_databases;

    private int batchExecuteValue = 0;

    private int firstInvoiceIndex = 0;

    private int sequentialInvoiceCount = 0;

    private int threadIndex = 0;
    int customerIndex = 0;
    int invoiceIndex = 0;

    private ReentrantLock lock;

    public DataGeneratorThreadSequentialInvoices(
            int threadindex, int batchExecuteValue, HashMap<String, String[]> sql_databases, 
            ReentrantLock lock, int sequentialInvoiceCount, 
            int customerIndex, int invoiceIndex, int firstInvoiceIndex) {
        this.threadIndex = threadindex;
        this.batchExecuteValue = batchExecuteValue;
        this.sequentialInvoiceCount = sequentialInvoiceCount;
        this.customerIndex = customerIndex;
        this.invoiceIndex = invoiceIndex;
        this.firstInvoiceIndex = firstInvoiceIndex;
        this.sql_databases = sql_databases;
        this.lock = lock;
    }

    public void run() {
        try {
            List<HashMap> preparedStatementsList = new ArrayList();
            List<Connection> connectionList = new ArrayList();
            
            for (String db_url : sql_databases.keySet()) {
                String[] db_info = sql_databases.get(db_url);
                String db_driver = db_info[0];
                String db_username = db_info[1];
                String db_password = db_info[2];
                
                Class.forName(db_driver);
                Connection connection = DriverManager.getConnection(db_url + "warehouse", db_username, db_password);
                
                connectionList.add(connection);
                PreparedStatement invoice = connection.prepareStatement(
                        "INSERT INTO invoice (id, customerId, state, duedate, previousinvoice) VALUES (?,?,?,?,?)");
                HashMap<String, PreparedStatement> preparedStatements = new HashMap<String, PreparedStatement>();
                
                preparedStatements.put("invoice", invoice);
                preparedStatementsList.add(preparedStatements);
            }
            for (int iterator = 0; iterator < sequentialInvoiceCount; iterator++) {
                insertSequentialInvoices(iterator, batchExecuteValue, preparedStatementsList);
                invoiceIndex++;
            }
            for (Connection connection : connectionList) {
                connection.close();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void insertSequentialInvoices(
            int iterator, int batchExecuteValue, List<HashMap> preparedStatementsList) throws SQLException {
        PreparedStatement invoice;
        String sqlInsert;
        String cypherCreate;
        Random r = new Random();
        
        r.setSeed(invoiceIndex);
        //-- 0 = incomplete, 1 = complete, 2 = sent, 3 = paid
        int state = 1 + r.nextInt(3);
        GregorianCalendar gregorianCalendar = new GregorianCalendar();
        int year = Calendar.getInstance().get(Calendar.YEAR);
        gregorianCalendar.set(gregorianCalendar.YEAR, year);
        int dayOfYear = 1 + r.nextInt(gregorianCalendar.getActualMaximum(gregorianCalendar.DAY_OF_YEAR));
        gregorianCalendar.set(gregorianCalendar.DAY_OF_YEAR, dayOfYear);
        java.util.Date dueDate = gregorianCalendar.getTime();
        java.sql.Date sqlDueDate = new java.sql.Date(gregorianCalendar.getTime().getTime());
        DateFormat dateFormat = new SimpleDateFormat("dd-MM-yyyy");
        String dueDateAsString = dateFormat.format(dueDate);
        
        for (HashMap<String, PreparedStatement> preparedStatements : preparedStatementsList) {
            invoice = preparedStatements.get("invoice");
            invoice.setInt(1, invoiceIndex);
            invoice.setInt(2, customerIndex);
            invoice.setInt(3, state);
            invoice.setDate(4, sqlDueDate, gregorianCalendar);
            if (invoiceIndex == firstInvoiceIndex) {
                sqlInsert = "INSERT INTO invoice (id, customerId, state, duedate, previousinvoice) VALUES (" + 
                        invoiceIndex + "," + customerIndex + "," + state + ",STR_TO_DATE('" + dueDateAsString + 
                        "','%d-%m-%Y')," + invoiceIndex + ")";
                invoice.setInt(5, invoiceIndex);
            } else {
                sqlInsert = "INSERT INTO invoice (id, customerId, state, duedate, previousinvoice) VALUES (" + 
                        invoiceIndex + "," + customerIndex + "," + state + ",STR_TO_DATE('" + dueDateAsString + 
                        "','%d-%m-%Y')," + (invoiceIndex - 1) + ")";
                invoice.setInt(5, invoiceIndex - 1);
            }
            invoice.addBatch();
        }
        LocalDate localDate = dueDate.toInstant().atZone(ZoneId.systemDefault()).toLocalDate();
        int month = localDate.getMonthValue();
        int day = localDate.getDayOfMonth();
        r.setSeed(invoiceIndex);
        int discountPercent = 1 + r.nextInt(101);
        double discount = (0.01 * discountPercent);
        if (iterator % batchExecuteValue == 0 || iterator == (sequentialInvoiceCount - 1)) {
            for (HashMap<String, PreparedStatement> preparedStatements : preparedStatementsList) {
                invoice = preparedStatements.get("invoice");
                invoice.executeBatch();
            }
        }
    }
}