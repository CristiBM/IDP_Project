using System;
using System.Collections.Generic;
using System.Data;
using System.Linq;
using System.Text;
using System.Threading;

using MySql.Data;
using MySql.Data.MySqlClient;

using Newtonsoft.Json;

using StackExchange.Redis;


namespace ConsoleApp1
{
    class Program
    {
        static void Main(string[] args)
        {
            /*
                Wait 15s for the initialization of the databases
            */
            Thread.Sleep(15000);
            Console.WriteLine("Hello, world!");

            MySqlConnection mysqlConn = new MySqlConnection();
            mysqlConn.ConnectionString = "server=db;user=root;database=tutorFinder;port=3306;password=root";
            MySqlCommand cmd1 = new MySqlCommand();
            MySqlCommand cmd2 = new MySqlCommand();
            MySqlCommand cmd3 = new MySqlCommand();
            
            try
            {
                var redisConn = ConnectionMultiplexer.Connect("redis:6379,Password=root");
                var redis = redisConn.GetDatabase();

                mysqlConn.Open();
                cmd1.Connection = mysqlConn;
                cmd2.Connection = mysqlConn;
                cmd3.Connection = mysqlConn;

                while (true)
                {
                    Thread.Sleep(100);

                    var userDataTemplate = new {
                        username = "",
                        password = "",
                        name = "",
                        address = "",
                        mail = "",
                        phone = ""
                    };
                    string json = redis.ListLeftPopAsync("queue:users").Result;
                    if (json != null)
                    {
                        var userData = JsonConvert.DeserializeAnonymousType(json, userDataTemplate);
                        Console.WriteLine($"Processing '{userData.name}' by '{userData.password}'");
                        
                        cmd1.CommandText = "createUser";
                        cmd1.CommandType = CommandType.StoredProcedure;
                        cmd1.Parameters.AddWithValue("@userName", userData.username);
                        cmd1.Parameters["@userName"].Direction = ParameterDirection.Input;
                        
                        cmd1.Parameters.AddWithValue("@passwd", userData.password);
                        cmd1.Parameters["@passwd"].Direction = ParameterDirection.Input;
                        
                        cmd1.Parameters.AddWithValue("@name", userData.name);
                        cmd1.Parameters["@name"].Direction = ParameterDirection.Input;
                        
                        cmd1.Parameters.AddWithValue("@address", userData.address);
                        cmd1.Parameters["@address"].Direction = ParameterDirection.Input;
                        
                        cmd1.Parameters.AddWithValue("@mail", userData.mail);
                        cmd1.Parameters["@mail"].Direction = ParameterDirection.Input;
                        
                        cmd1.Parameters.AddWithValue("@phoneNo", userData.phone);
                        cmd1.Parameters["@phoneNo"].Direction = ParameterDirection.Input;
                        
                        cmd1.ExecuteNonQuery();

                        cmd1.Parameters.Clear();
                        Console.WriteLine("createUser procedure was called");
                    }

                    var tutorDataTemplate = new {
                        tutid = "",
                        user = "",
                        subject = "",
                        xp = "",
                        channel = "",
                        price = ""
                    };
                    json = redis.ListLeftPopAsync("queue:tutors").Result;
                    if (json != null)
                    {
                        var tutorData = JsonConvert.DeserializeAnonymousType(json, tutorDataTemplate);

                        Console.WriteLine($"Processing tutor data: '{tutorData.user}'");
                        
                        cmd2.CommandText = "createTutor";
                        cmd2.CommandType = CommandType.StoredProcedure;
                        cmd2.Parameters.AddWithValue("@tutId", tutorData.tutid);
                        cmd2.Parameters["@tutId"].Direction = ParameterDirection.Input;
                        
                        cmd2.Parameters.AddWithValue("@userName", tutorData.user);
                        cmd2.Parameters["@userName"].Direction = ParameterDirection.Input;
                        
                        cmd2.Parameters.AddWithValue("@subject", tutorData.subject);
                        cmd2.Parameters["@subject"].Direction = ParameterDirection.Input;
                        
                        cmd2.Parameters.AddWithValue("@experience", tutorData.xp);
                        cmd2.Parameters["@experience"].Direction = ParameterDirection.Input;
                        
                        cmd2.Parameters.AddWithValue("@channel", tutorData.channel);
                        cmd2.Parameters["@channel"].Direction = ParameterDirection.Input;
                        
                        cmd2.Parameters.AddWithValue("@price", tutorData.price);
                        cmd2.Parameters["@price"].Direction = ParameterDirection.Input;
                        
                        cmd2.ExecuteNonQuery();

                        cmd2.Parameters.Clear();
                        Console.WriteLine("createTutor procedure was called");
                    }

                    var matchDataTemplate = new {
                        tutor = "",
                        student = ""
                    };
                    json = redis.ListLeftPopAsync("queue:matches").Result;
                    if (json != null)
                    {
                        var matchData = JsonConvert.DeserializeAnonymousType(json, matchDataTemplate);

                        Console.WriteLine($"Processing a match: '{matchData.tutor}', '{matchData.student}'");
                    
                        cmd3.CommandText = "insertMatch";
                        cmd3.CommandType = CommandType.StoredProcedure;
                        cmd3.Parameters.AddWithValue("@tutId", matchData.tutor);
                        cmd3.Parameters["@tutId"].Direction = ParameterDirection.Input;
                        
                        cmd3.Parameters.AddWithValue("@studentUsername", matchData.student);
                        cmd3.Parameters["@studentUsername"].Direction = ParameterDirection.Input;

                        cmd3.ExecuteNonQuery();

                        cmd3.Parameters.Clear();
                        Console.WriteLine("insertMatch procedure was called");                    
                    }
                }
            }
            catch (Exception e)
            {
                Console.WriteLine("Error has occured: " + e.ToString());
            }
            mysqlConn.Close();
            Console.WriteLine("Worker Done!");
        }
    }
}
