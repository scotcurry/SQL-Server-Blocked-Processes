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