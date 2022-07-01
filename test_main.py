import main
import unittest

class MainTest(unittest.TestCase):
    

    def db_conn(self):
        test_conn = main.makeDb_connection()
        if (test_conn):
        # Carry out normal procedure
            print("Connection successful")
            test_conn.close()
            assert True
        else:
    # Terminate
            print("Connection unsuccessful")
            test_conn.close()
            assert False
    
    def db_query(self):
        test_conn = main.makeDb_connection()
        mycursor = test_conn.cursor()
        sql = '''SELECT name,address, available, phone, SQRT(4) AS distance, website
        FROM alberta HAVING distance < 1000 ORDER BY distance LIMIT 1;'''
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        if len(myresult) != 0:
            assert True
        else:
            assert False

if __name__ == '__main__':
    unittest.main()
