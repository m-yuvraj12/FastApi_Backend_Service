# Minimal Android receiver (Kotlin)

Goal: an app that shows its FCM token (so you can register it via Swagger) and displays notifications.

## 1. Firebase
1. https://console.firebase.google.com → **Add project**.
2. **Add app → Android**. Package name e.g. `com.example.pushdemo`. Download `google-services.json` → put in `app/`.
3. **Project settings → Service accounts → Generate new private key** → save as
   `secrets/firebase-service-account.json` in this repo (it is git-ignored).

## 2. Gradle
Project-level `build.gradle.kts`: `id("com.google.gms.google-services") version "4.4.2" apply false`

App-level `build.gradle.kts`: add plugin `id("com.google.gms.google-services")` and

```kotlin
dependencies {
    implementation(platform("com.google.firebase:firebase-bom:33.7.0"))
    implementation("com.google.firebase:firebase-messaging")
}
```

## 3. AndroidManifest.xml
```xml
<uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>
<application ...>
    <service android:name=".PushService" android:exported="false">
        <intent-filter><action android:name="com.google.firebase.MESSAGING_EVENT"/></intent-filter>
    </service>
    ...
</application>
```

## 4. MainActivity.kt
```kotlin
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val tv = TextView(this).apply { setTextIsSelectable(true); setPadding(48, 96, 48, 48) }
        setContentView(tv)

        if (Build.VERSION.SDK_INT >= 33) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1)
        }
        FirebaseMessaging.getInstance().token.addOnCompleteListener {
            val token = it.result
            Log.d("FCM", token)
            tv.text = "FCM token (long-press to copy):\n\n$token"
        }
    }
}
```

## 5. PushService.kt (shows notifications while the app is in the foreground)
When the app is in the background, FCM displays the notification automatically.
```kotlin
class PushService : FirebaseMessagingService() {
    override fun onMessageReceived(msg: RemoteMessage) {
        val n = msg.notification ?: return
        val channelId = "default"
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(NotificationChannel(channelId, "General", NotificationManager.IMPORTANCE_HIGH))
        nm.notify(System.currentTimeMillis().toInt(),
            NotificationCompat.Builder(this, channelId)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle(n.title).setContentText(n.body).setAutoCancel(true).build())
    }
    override fun onNewToken(token: String) { Log.d("FCM", "new token: $token") }
}
```

Run on a physical device or an emulator image **with Google Play** (FCM needs Play Services).
