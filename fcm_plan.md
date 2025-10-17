# React Native FCM Implementation Plan

This document outlines the steps required to integrate Firebase Cloud Messaging (FCM) into the React Native client application to receive push notifications from the backend.

## Prerequisites

- React Native project with Firebase already configured (as mentioned in the task).
- Firebase project set up with FCM enabled.

## Implementation Steps

### 1. Install React Native Firebase Messaging

Add the messaging module to your React Native project:

```bash
npm install @react-native-firebase/messaging
# or
yarn add @react-native-firebase/messaging
```

For iOS, also install the pods:
```bash
cd ios && pod install
```

### 2. Configure Firebase in React Native

Ensure your `firebase.json` or Firebase configuration is properly set up. The messaging module should automatically use your existing Firebase configuration.

### 3. Request Notification Permissions

In your main App component or a dedicated service file, request notification permissions on app launch:

```javascript
import messaging from '@react-native-firebase/messaging';

// Request permission (iOS only - Android automatically grants)
async function requestUserPermission() {
  const authStatus = await messaging().requestPermission();
  const enabled =
    authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
    authStatus === messaging.AuthorizationStatus.PROVISIONAL;

  if (enabled) {
    console.log('Authorization status:', authStatus);
  }
}

// Call this in your App.js or main component
useEffect(() => {
  requestUserPermission();
}, []);
```

### 4. Get FCM Token

Retrieve the FCM token and send it to your backend to store with the user's profile:

```javascript
import messaging from '@react-native-firebase/messaging';

// Function to get FCM token
async function getFCMToken() {
  const fcmToken = await messaging().getToken();
  if (fcmToken) {
    console.log('FCM Token:', fcmToken);
    // Send this token to your backend API
    // Example: await api.updateUserFCMToken(fcmToken);
  } else {
    console.log('Failed to get FCM token');
  }
}

// Call this after login or when user profile is available
useEffect(() => {
  getFCMToken();
}, []);
```

### 5. Handle Notifications

Implement handlers for different app states:

```javascript
import messaging from '@react-native-firebase/messaging';

// Handle foreground notifications
messaging().onMessage(async remoteMessage => {
  console.log('Foreground message:', remoteMessage);
  // Display local notification or update UI
  // You can use a library like @notifee/react-native for custom notifications
});

// Handle background/terminated state notifications
messaging().setBackgroundMessageHandler(async remoteMessage => {
  console.log('Background message:', remoteMessage);
  // Process the message (e.g., update app state, show notification)
});

// Handle notification tap when app is in background/terminated
messaging().onNotificationOpenedApp(remoteMessage => {
  console.log('Notification opened app:', remoteMessage);
  // Navigate to relevant screen based on notification data
  // e.g., navigate to order details screen
});

// Handle notification tap when app is terminated
messaging()
  .getInitialNotification()
  .then(remoteMessage => {
    if (remoteMessage) {
      console.log('App opened from terminated state:', remoteMessage);
      // Navigate to relevant screen
    }
  });
```

### 6. Backend API Integration

Create an API endpoint in your backend to receive and store the FCM token. Update your user profile API to include the FCM token field.

Example API call from React Native:

```javascript
// After getting FCM token
const updateFCMToken = async (token) => {
  try {
    const response = await fetch('YOUR_BACKEND_API/user/update-fcm-token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userToken}`, // Your auth token
      },
      body: JSON.stringify({ fcmToken: token }),
    });
    const result = await response.json();
    console.log('FCM token updated:', result);
  } catch (error) {
    console.error('Error updating FCM token:', error);
  }
};
```

### 7. Notification Data Handling

Process the custom data payload from notifications:

```javascript
// In your message handlers
const handleNotificationData = (remoteMessage) => {
  const { data } = remoteMessage;
  if (data) {
    switch (data.type) {
      case 'ORDER_ACCEPTED':
        // Navigate to order tracking screen
        // Update order status in local state
        break;
      case 'DRIVER_NEAR':
        // Show alert or update UI to indicate driver is near
        break;
      default:
        // Handle other notification types
        break;
    }
  }
};
```

### 8. Testing

1. Build and run your app on a physical device (FCM doesn't work reliably on simulators).
2. Use Firebase Console to send test notifications.
3. Test different app states: foreground, background, and terminated.
4. Verify that notifications trigger the correct actions in your app.

### 9. Additional Considerations

- **iOS Specific:** Ensure you have proper APNs certificates configured in Firebase for iOS notifications.
- **Android Specific:** Notifications should work out of the box, but you may want to customize the notification channel.
- **Security:** Never expose FCM tokens in logs or send them to untrusted servers.
- **Token Refresh:** FCM tokens can change, so implement a mechanism to update the token on the backend when it changes.
- **Offline Handling:** Consider how to handle notifications when the device is offline.

### 10. Libraries for Enhanced UX

Consider using additional libraries for better notification handling:
- `@notifee/react-native`: For advanced notification customization
- `react-native-push-notification`: Alternative FCM implementation
- `@react-native-async-storage/async-storage`: To store notification preferences locally

This plan provides a complete implementation for receiving push notifications in your React Native app. The backend will handle sending notifications based on the triggers you specified (driver accepts order and driver near client).