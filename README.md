# Information to Build Widget Showning Blocked SQL Server Processes

> Built on a Custom Check to retrieve the data and table widget to visualize the data

## [Custom Check](https://docs.datadoghq.com/developers/write_agent_check/?tab=agentv6v7)

Create a file named blocked_sql_processes.yaml in the Datadog conf.d folder.  See [agent documentation](https://docs.datadoghq.com/agent/) for locations.

### blocked_sql_processes.yaml code
```
instances: 
  - {}
```

Create a file called blocked_sql_processes.py in the check.d folder and enter the following code.  See [agent documentation](https://docs.datadoghq.com/agent/) for locations.

### blocked_sql_processes.py code
```
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
```

## [Configuring SQL Server to Show Blocked Processes](https://learn.microsoft.com/en-us/sql/database-engine/configure-windows/blocked-process-threshold-server-configuration-option?view=sql-server-ver16)

> The following SQL Server script (run against the master database) sets the threshold time that SQL Server uses to check for blocked processes.  Work with you DBA for optimal timing in your environment.

```
sp_configure 'show advanced options', 1;
GO
RECONFIGURE
GO
sp_configure 'blocked process threshold', 6;
GO
RECONFIGURE ;
GO
```

## Test Scripts

> While you may know that you have blocked processes in your environment, the scripts below are examples of how to force a blocked process.  Please note that these are built to run against the [AdventureWorks example database](https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure?view=sql-server-ver16&tabs=ssms).

Run the scripts in the order:
* UpdateProductPriceWithWait.sql
* UpdateProdcutPriceWithNoWait.sql
* SPIDWithSQLStatement.sql

### UpdateProductPriceWithWait.sql

```
BEGIN TRANSACTION
UPDATE Production.Product
SET StandardCost = 10.00
WHERE Production.Product.ProductID = 1
WAITFOR DELAY '00:10:00.000'
COMMIT
```

### UpdateProductPriceWithNoWait.sql
```
BEGIN TRANSACTION
UPDATE Production.Product
SET StandardCost = 10.00
WHERE Production.Product.ProductID = 1
COMMIT
```

### SPIDWithSQLStatement.sql
```
SELECT   SPID       = exreq.session_id
    ,STATUS         = ses.STATUS
    ,[Login]        = ses.login_name
    ,Host           = ses.host_name
    ,BlkBy          = exreq.blocking_session_id
    ,DBName         = DB_Name(exreq.database_id)
    ,CommandType    = exreq.command
    ,ObjectName     = OBJECT_NAME(sqtext.objectid)
    ,CPUTime        = exreq.cpu_time
    ,StartTime      = exreq.start_time
    ,TimeElapsed    = CAST(GETDATE() - exreq.start_time AS TIME)
    ,SQLStatement   = sqtext.text
FROM    sys.dm_exec_requests exreq
    OUTER APPLY sys.dm_exec_sql_text(exreq.sql_handle) sqtext
    LEFT JOIN sys.dm_exec_sessions ses
    ON ses.session_id = exreq.session_id
LEFT JOIN sys.dm_exec_connections con
    ON con.session_id = ses.session_id
WHERE   sqtext.text IS NOT NULL
```

When the query above is run you should see a blocked process returned.  If that is the case, check the Datadog console and search **Logs**.

## Create facets

> The easiest way to build the associated dashboard is to run the log entries into facets.  Select one of the log entries.  They will look like the following:

```
{
	"database_name": "AdventureWorks2019",
	"blocked_by_spid": 63,
	"host": "WIN2019SERVER",
	"elapsed_time": "00:09:36.4633333",
	"login": "scot",
	"spid": 69
}
```

## Dashboard - Table Widget

> Below is a starter table widget for displaying the blocked processes.

```
{"title":"Doing Scot's Work for him, will take payment directly from wages","description":null,"widgets":[{"id":215873905097458,"layout":{"x":1,"y":2,"width":54,"height":32},"definition":{"title":"Blocked Process Table","title_size":"16","title_align":"left","time":{},"type":"query_table","requests":[{"queries":[{"data_source":"logs","name":"query1","indexes":["*"],"compute":{"aggregation":"cardinality","metric":"@spid"},"group_by":[{"facet":"@spid","limit":5,"sort":{"order":"desc","aggregation":"cardinality","metric":"@spid"}},{"facet":"@blocked_by_spid","limit":5,"sort":{"order":"desc","aggregation":"cardinality","metric":"@spid"}},{"facet":"@host","limit":5,"sort":{"order":"desc","aggregation":"cardinality","metric":"@spid"}},{"facet":"@elapsed_time","limit":5,"sort":{"order":"desc","aggregation":"cardinality","metric":"@spid"}}],"search":{"query":"source:blocked_sql_processes"},"storage":"hot"}],"formulas":[{"conditional_formats":[],"cell_display_mode":"bar","formula":"query1","limit":{"count":50,"order":"desc"}}],"response_format":"scalar","text_formats":[[],[],[],[{"match":{"type":"contains","value":"00:01"},"palette":"white_on_yellow"},{"match":{"type":"contains","value":"00:00"},"palette":"white_on_green"}]]}],"has_search_bar":"auto"}}],"template_variables":[],"layout_type":"free","notify_list":[]}
```