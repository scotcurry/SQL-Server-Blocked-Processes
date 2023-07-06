import requests
import pyodbc
import json

try:
    from datadog_checks.base import AgentCheck
except ImportError:
    from checks import AgentCheck

__version__ = "1.0.0"

class GetBlockedSQLProcessesCheck(AgentCheck):
    def check(self, instance):
     # Might need to be updated for connection trust.
        conn = pyodbc.connect('Driver={SQL Server};'
                              'Server=localhost;'
                              'Database=master;'
                              'Trusted_Connection=yes;')

     # Just a long command so it is broken into lines 
        sql_command = ('SELECT SPID = exreq.session_id, '
                            'STATUS = ses.STATUS, '
                            '[Login] = ses.login_name, '
                            'Host = ses.host_name, '
                            'BlkBy = exreq.blocking_session_id, '
                            'DBName = DB_Name(exreq.database_id), '
                            'CommandType = exreq.command, '
                            'CPUTime = exreq.cpu_time, '
                            'StartTime = exreq.start_time, '
                            'TimeElapsed = CAST(GETDATE() - exreq.start_time AS TIME), '
                            'SQLStatement = sqtext.text '
                       'FROM sys.dm_exec_requests exreq '
                            'OUTER APPLY sys.dm_exec_sql_text(exreq.sql_handle) sqtext '
                            'LEFT JOIN sys.dm_exec_sessions ses '
                            'ON ses.session_id = exreq.session_id '
                       'LEFT JOIN sys.dm_exec_connections con '
                            'ON con.session_id = ses.session_id '
                       'WHERE sqtext.text IS NOT NULL '
                       'AND exreq.blocking_session_id != 0')

        # print(str(sql_command))
        # print('Connected to Database')
        cursor = conn.cursor()
        cursor.execute(sql_command)

        # Going to make calls to post the log entries so setup is done here.
        headers = { 'Content-Type': 'application/json', 'DD-API-KEY': "47f389b365cc57292168914a79ae5f47" }

        for row in cursor:
            spid = row[0]
            login = row[2]
            host = row[3]
            blocked_by = row[4]
            database_name = row[5]
            elapsed_time = row[9]

            json_dict = { "spid": spid, "login": login, "host": host, "database_name": database_name, "elapsed_time": elapsed_time,
                       "blocked_by_spid": blocked_by, "ddsource": "blocked_sql_processes" }
            json_string = json.dumps(json_dict)
            # print(json_string)
            response = requests.post('https://http-intake.logs.datadoghq.com/v1/input', headers=headers, data=json_string)
            # print(response)