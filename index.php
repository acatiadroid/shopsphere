<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MyShop - Welcome</title>
<link rel="stylesheet" href="styles.css">
<style>
.header {
  background-color: #2c3e50;
  color: white;
  padding: 20px 0;
  text-align: center;
  margin-bottom: 30px;
}
.header h1 {
  margin: 0;
  font-size: 2.5em;
}
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}
.welcome-text {
  text-align: center;
  margin-bottom: 30px;
  font-size: 1.2em;
  color: #555;
}
.signup-link {
  display: inline-block;
  background-color: #007bff;
  color: white;
  padding: 12px 30px;
  text-decoration: none;
  border-radius: 4px;
  font-size: 18px;
  margin-top: 20px;
}
.signup-link:hover {
  background-color: #0056b3;
}
.users-section {
  margin-top: 50px;
  padding: 30px;
  background-color: #f8f9fa;
  border-radius: 8px;
}
.users-section h2 {
  color: #2c3e50;
  margin-bottom: 20px;
  text-align: center;
}
.users-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
  background-color: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.users-table th,
.users-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}
.users-table th {
  background-color: #2c3e50;
  color: white;
  font-weight: bold;
}
.users-table tr:hover {
  background-color: #f5f5f5;
}
.no-users {
  text-align: center;
  color: #666;
  font-style: italic;
  padding: 20px;
}
.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 20px;
  border: 1px solid #f5c6cb;
}
</style>
</head>
<body>
  <div class="header">
    <div class="container">
      <h1>MyShop</h1>
      <p>Your one-stop destination for amazing products</p>
    </div>
  </div>

  <div class="container">
    <div class="welcome-text">
      <h2>Welcome to MyShop</h2>
      <p>Join our community today to access exclusive deals and features!</p>

      <!-- Simple link to signup page -->
      <a href="register.php" class="signup-link">Create Your Account</a>
    </div>

    <div class="users-section">
      <h2>Our Community Members</h2>

      <?php
      // Database connection settings
      $serverName = "tcp:luke-shopsphere.database.windows.net,1433";
      $connectionOptions = [
          "Database" => "luke-database",
          "Uid" => "myadmin",
          "PWD" => "Abcdefgh0!",
          "Encrypt" => 1,
          "TrustServerCertificate" => 0,
      ];

      try {
          // Connect to database
          $conn = sqlsrv_connect($serverName, $connectionOptions);

          if ($conn) {
              // Query to get all users
              $sql = "SELECT name, email FROM shopusers ORDER BY name ASC";
              $stmt = sqlsrv_query($conn, $sql);

              if ($stmt) {
                  $users = [];
                  while ($row = sqlsrv_fetch_array($stmt, SQLSRV_FETCH_ASSOC)) {
                      $users[] = $row;
                  }

                  if (count($users) > 0) {
                      echo '<table class="users-table">';
                      echo "<thead>";
                      echo "<tr>";
                      echo "<th>Name</th>";
                      echo "<th>Email</th>";
                      echo "</tr>";
                      echo "</thead>";
                      echo "<tbody>";

                      foreach ($users as $user) {
                          echo "<tr>";
                          echo "<td>" .
                              htmlspecialchars($user["name"]) .
                              "</td>";
                          echo "<td>" .
                              htmlspecialchars($user["email"]) .
                              "</td>";
                          echo "</tr>";
                      }

                      echo "</tbody>";
                      echo "</table>";
                  } else {
                      echo '<div class="no-users">No users have registered yet. Be the first to join our community!</div>';
                  }

                  sqlsrv_free_stmt($stmt);
              } else {
                  $errors = sqlsrv_errors();
                  echo '<div class="error-message">Error retrieving users: ';
                  if ($errors != null) {
                      foreach ($errors as $error) {
                          echo htmlspecialchars($error["message"]);
                      }
                  }
                  echo "</div>";
              }

              sqlsrv_close($conn);
          } else {
              $connection_errors = sqlsrv_errors();
              echo '<div class="error-message">Database connection failed: ';
              if ($connection_errors != null) {
                  foreach ($connection_errors as $error) {
                      echo htmlspecialchars($error["message"]);
                  }
              }
              echo "</div>";
          }
      } catch (Exception $e) {
          echo '<div class="error-message">An error occurred: ' .
              htmlspecialchars($e->getMessage()) .
              "</div>";
      }
      ?>
    </div>
  </div>
</body>
</html>
