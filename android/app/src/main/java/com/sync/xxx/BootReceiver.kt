package com.sync.xxx

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.core.content.ContextCompat

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        val action = intent?.action ?: return
        if (action == Intent.ACTION_BOOT_COMPLETED ||
            action == "android.intent.action.QUICKBOOT_POWERON" ||
            action == Intent.ACTION_MY_PACKAGE_REPLACED ||
            action == Intent.ACTION_LOCKED_BOOT_COMPLETED) {

            try {
                val serviceIntent = Intent(context, DeviceService::class.java)
                ContextCompat.startForegroundService(context, serviceIntent)
            } catch (e: Exception) {
                android.util.Log.e("BootReceiver", "start DeviceService: ${e.message}")
            }

            try {
                if (LockPersist.isLocked(context)) {
                    android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                        LockPersist.reapply(context)
                    }, 2500)
                }
            } catch (e: Exception) {
                android.util.Log.e("BootReceiver", "reapply lock: ${e.message}")
            }
        }
    }
}
