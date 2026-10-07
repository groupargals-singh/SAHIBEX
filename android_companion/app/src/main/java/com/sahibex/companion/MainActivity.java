package com.sahibex.companion;

import android.app.Activity; import android.content.Intent; import android.os.Bundle; import android.provider.Settings; import android.widget.TextView; import java.security.SecureRandom; import android.content.SharedPreferences;

public final class MainActivity extends Activity {
 @Override protected void onCreate(Bundle state){super.onCreate(state);SharedPreferences p=getSharedPreferences("sahibex",MODE_PRIVATE);String token=p.getString("token",null);if(token==null){byte[] b=new byte[32];new SecureRandom().nextBytes(b);token=android.util.Base64.encodeToString(b,android.util.Base64.NO_WRAP|android.util.Base64.URL_SAFE);p.edit().putString("token",token).apply();}TextView v=new TextView(this);v.setText("SAHIBEX Android Companion\n\nEnable Accessibility Service.\n\nPairing token (keep private):\n"+token+"\n\nTap here to open Accessibility Settings.");v.setPadding(40,80,40,40);v.setOnClickListener(x->startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)));setContentView(v);}
}
