# WebSocket Tracking Guide

## Driver's Guide

### Overview
WebSocket enables real-time communication between the driver's app and the server, allowing live order tracking. This guide explains how drivers connect and send location updates.

### Setup
1. Add required packages to `pubspec.yaml`:
```yaml
dependencies:
  web_socket_channel: ^2.2.0
  location: ^4.3.0
```

2. Configure WebSocket client in `location_service.dart`:
```dart
import 'package:web_socket_channel/web_socket_channel.dart';

class LocationService {
  static WebSocketChannel? _channel;

  static Future<void> init() async {
    _channel = WebSocketChannel.connect(
      Uri.parse('wss://your-server.com/ws/driver'),
    );
  }
}
```

### Connection Handling
1. Establish connection on app start:
```dart
void main() {
  LocationService.init();
  runApp(MyApp());
}
```

2. Send location updates:
```dart
LocationService._channel?.sink?.add(
  jsonEncode({
    'lat': position.latitude,
    'lng': position.longitude,
    'orderId': currentOrder.id,
  }),
);
```

3. Handle errors:
```dart
LocationService._channel?.stream?.listen(
  (message) {},
  onError: (error) {
    print('WebSocket error: $error');
  },
  onDone: () {
    print('WebSocket connection closed');
  },
);
```

### Security Considerations
- Use secure WebSocket connections (wss://)
- Authenticate with tokens
- Encrypt sensitive data

## Client's Guide

### Overview
WebSocket allows clients to receive real-time order status and location updates. This section covers client-side implementation.

### Setup
1. Add client packages to `pubspec.yaml`:
```yaml
dependencies:
  web_socket_channel: ^2.2.0
  flutter_map: ^0.14.0
```

2. Integrate WebSocket in `order_detail_screen.dart`:
```dart
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class OrderDetailScreen extends StatefulWidget {
  @override
  _OrderDetailScreenState createState() => _OrderDetailScreenState();
}

class _OrderDetailScreenState extends State<OrderDetailScreen> {
  WebSocketChannel? _channel;

  @override
  void initState() {
    super.initState();
    _channel = WebSocketChannel.connect(
      Uri.parse('wss://your-server.com/ws/client'),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text('Order Tracking'),
      ),
    );
  }
}
```

### Connection Handling
1. Establish connection when viewing an order:
```dart
void _startTrackingOrder() {
  _channel = WebSocketChannel.connect(
    Uri.parse('wss://your-server.com/ws/client/${widget.orderId}'),
  );
}
```

2. Receive and handle updates:
```dart
@override
void initState() {
  super.initState();
  _channel?.stream?.listen(
    (message) {
      final update = jsonDecode(message);
      if (update['status'] == 'delivered') {
        // Update UI accordingly
      }
    },
    onError: (error) {
      print('Client error: $error');
    },
    onDone: () {
      print('Client connection closed');
    },
  );
}
```

### Security Considerations
- Validate received data
- Use secure connections
- Handle sensitive information securely

## Admin's Guide

### Overview
Admins monitor and manage WebSocket connections for drivers and clients, ensuring smooth order tracking.

### Setup
1. Set up server with WebSocket support:
```bash
npm install express-ws
```

2. Configure server in `server.js`:
```javascript
const express = require('express');
const WebSocket = require('ws');
const app = express();
const server = app.listen(8080, () => {
  console.log('Server running on port 8080');
});

const wss = new WebSocket.Server({ server });

wss.on('connection', (ws) => {
  console.log('New client connected');
  
  ws.on('message', (message) => {
    // Handle incoming messages
  });
  
  ws.on('close', () => {
    console.log('Client disconnected');
  });
});
```

### Connection Handling
1. Monitor driver connections:
```javascript
wss.on('connection', (ws, req) => {
  const ip = req.socket.remoteAddress;
  console.log(`Driver connected from ${ip}`);
  
  ws.on('message', (message) => {
    const data = JSON.parse(message);
    if (data.type === 'location_update') {
      // Update order location
    }
  });
});
```

2. Broadcast updates to clients:
```javascript
function broadcast(message) {
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(message);
    }
  });
}
```

3. Handle admin commands:
```javascript
app.post('/admin/update', (req, res) => {
  const orderId = req.body.orderId;
  const status = req.body.status;
  broadcast(JSON.stringify({
    orderId: orderId,
    status: status
  }));
  res.send('Update broadcasted');
});
```

### Security Considerations
- Implement rate limiting
- Use secure WebSocket connections
- Log all activities
- Set up proper access controls
