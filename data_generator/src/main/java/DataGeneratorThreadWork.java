import java.sql.*;
import java.util.*;
import java.util.concurrent.locks.ReentrantLock;

public class DataGeneratorThreadWork extends Thread {

    private HashMap<String, String[]> sql_databases;

    private int iterationCount = 0;
    private int batchExecuteValue = 0;

    private int threadIndex = 0;

    private int workIndex = 0;
    private int itemFactor = 0;
    private int itemCount = 0;
    private int workTypeFactor = 0;
    private int workTypeCount = 0;

    private ReentrantLock lock;

    public DataGeneratorThreadWork(
            int threadIndex, int iterationCount, int batchExecuteValue, HashMap<String, String[]> sql_databases, 
            ReentrantLock lock, int workIndex, int itemFactor, int itemCount, 
            int workTypeFactor, int workTypeCount) {
        this.threadIndex = threadIndex;
        this.iterationCount = iterationCount;
        this.batchExecuteValue = batchExecuteValue;
        this.workIndex = workIndex;
        this.itemFactor = itemFactor;
        this.itemCount = itemCount;
        this.workTypeFactor = workTypeFactor;
        this.workTypeCount = workTypeCount;
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
                PreparedStatement work = connection.prepareStatement(
                        "INSERT INTO work (id, name) VALUES (?,?)");
                PreparedStatement usedItem = connection.prepareStatement(
                        "INSERT INTO useditem (amount, discount, workId, itemId) VALUES(?,?,?,?)");
                PreparedStatement workHours = connection.prepareStatement(
                        "INSERT INTO workhours (worktypeId, hours, discount, workId) VALUES(?,?,?,?)");
                HashMap<String, PreparedStatement> preparedStatements = new HashMap<String, PreparedStatement>();
                
                preparedStatements.put("work", work);
                preparedStatements.put("useditem", usedItem);
                preparedStatements.put("workhours", workHours);
                preparedStatementsList.add(preparedStatements);
            }
            for (int iterator = 0; iterator < iterationCount; iterator++) {
                insertWork(iterator, batchExecuteValue, preparedStatementsList);
            }
            for (Connection connection : connectionList) {
                connection.close();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public List<Integer> getItemIndexes(int index) {
        List<Integer> allItemIndexes = new ArrayList<Integer>();
        
        for (int i = 0; i < itemCount; i++) {
            allItemIndexes.add(i);
        }
        Collections.shuffle(allItemIndexes, new Random(index));
        List<Integer> selectedItemIndexes = allItemIndexes.subList(0, itemFactor);
        
        return selectedItemIndexes;
    }

    public List<Integer> getWorkTypeIndexes(int index) {
        List<Integer> allWorkTypeIndexes = new ArrayList<Integer>();
        
        for (int i = 0; i < workTypeCount; i++) {
            allWorkTypeIndexes.add(i);
        }
        Collections.shuffle(allWorkTypeIndexes, new Random(index));
        List<Integer> selectedWorkTypeIndexes = allWorkTypeIndexes.subList(0, workTypeFactor);
        
        return selectedWorkTypeIndexes;
    }

    public void insertWork(int iterator, int batchExecuteValue, List<HashMap> preparedStatementsList) 
            throws SQLException {
        PreparedStatement work;
        PreparedStatement usedItem;
        PreparedStatement workHours;
        
        System.out.println("Thread: " + threadIndex + " workIndex: " + workIndex);
        int workIndexOriginal = workIndex;
        String workName = "Generic " + workIndex;
        String sqlInsert = "INSERT INTO work (id, name) VALUES (" + workIndex + ",'" + workName + "')";
        
        for (HashMap<String, PreparedStatement> preparedStatements : preparedStatementsList) {
            work = preparedStatements.get("work");
            work.setInt(1, workIndex);
            work.setString(2, workName);
            work.addBatch();
        }
        String cypherCreate = "CREATE (s:work {workId: " + workIndex + ", name: \"" + workName + "\"})";
        Random r = new Random(workIndex);
        int discountPercent = 1 + r.nextInt(101);
        double discount = (0.01 * discountPercent);
        List<Integer> itemIndexes = getItemIndexes(workIndex);
        //System.out.println("itemIndexes");
        //System.out.println(itemIndexes.toString());
        int i = 0;
        while (i < itemIndexes.size()) {
            r.setSeed(workIndex);
            int amount = 1 + r.nextInt(101);
            int itemId = itemIndexes.get(i);
            sqlInsert = "INSERT INTO useditem (amount, discount, workId, itemId) VALUES(" + amount + "," + 
                    discount + "," + workIndex + "," + itemId + ")";
            for (HashMap<String, PreparedStatement> preparedStatements : preparedStatementsList) {
                usedItem = preparedStatements.get("useditem");
                usedItem.setInt(1, amount);
                usedItem.setDouble(2, discount);
                usedItem.setInt(3, workIndex);
                usedItem.setInt(4, itemId);
                usedItem.addBatch();
            }
            i++;
        }
        List<Integer> workTypeIndexes = getWorkTypeIndexes(workIndex);
        //System.out.println("workTypeIndexes");
        //System.out.println(workTypeIndexes.toString());
        i = 0;
        while (i < workTypeIndexes.size()) {
            r.setSeed(workIndex);
            int hours = r.nextInt(100);
            int worktypeId = workTypeIndexes.get(i);
            sqlInsert = "INSERT INTO workhours (worktypeId, hours, discount, workId) VALUES(" + worktypeId + 
                    "," + hours + "," + discount + "," + workIndex + ")";
            for (HashMap<String, PreparedStatement> preparedStatements : preparedStatementsList) {
                workHours = preparedStatements.get("workhours");
                workHours.setInt(1, worktypeId);
                workHours.setInt(2, hours);
                workHours.setDouble(3, discount);
                workHours.setInt(4, workIndex);
                workHours.addBatch();
            }
            i++;
        }
        workIndex++;
        if (iterator % batchExecuteValue == 0 || iterator == (iterationCount - 1)) {
            for (HashMap<String, PreparedStatement> preparedStatements : preparedStatementsList) {
                work = preparedStatements.get("work");
                usedItem = preparedStatements.get("useditem");
                workHours = preparedStatements.get("workhours");
                work.executeBatch();
                usedItem.executeBatch();
                workHours.executeBatch();
            }
        }
    }
}