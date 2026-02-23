#include <WiFiNINA.h>
#include <Arduino_LSM6DSOX.h>

char ssid[] = "rahool";
char pass[] = "rahooligan56";

WiFiClient client;

const char* server = "172.20.10.12";  // Your computer IP
int port = 3000;

unsigned long lastSampleTime = 0;
const unsigned long sampleInterval = 5000; // 200 Hz (5000 microseconds)

void setup() {
  Serial.begin(115200);
  while (!Serial);

  if (!IMU.begin()) {
    Serial.println("IMU failed!");
    while (1);
  }

  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, pass);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected to WiFi");

  Serial.println("Connecting to server...");
  while (!client.connect(server, port)) {
    delay(1000);
    Serial.println("Retrying...");
  }

  Serial.println("Connected to server!");
}

void loop() {

  if (!client.connected()) {
    client.connect(server, port);
  }

  unsigned long currentMicros = micros();

  if (currentMicros - lastSampleTime >= sampleInterval) {
    lastSampleTime = currentMicros;

    float ax, ay, az;
    float gx, gy, gz;

    if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
      IMU.readAcceleration(ax, ay, az);
      IMU.readGyroscope(gx, gy, gz);

      client.print(millis());
      client.print(",");
      client.print(ax, 5);
      client.print(",");
      client.print(ay, 5);
      client.print(",");
      client.print(az, 5);
      client.print(",");
      client.print(gx, 5);
      client.print(",");
      client.print(gy, 5);
      client.print(",");
      client.println(gz, 5);
    }
  }
}