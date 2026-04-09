# Network Access Guide

## Access LLM Debate from Other Devices

### Quick Start

**Start the Docker container:**
```bash
./docker-start.sh
```

This will display your network URL. For example:
```
📍 Server Information:
   Local:   http://localhost:8000
   Network: http://192.168.1.40:8000
```

### Access from Other Devices

On any device on the same network (phone, tablet, another computer):

1. **Open your browser**
2. **Navigate to:** `http://192.168.1.40:8000` (use your actual IP)
3. **Start debating!**

### Your Server IP

Your server is accessible at: **192.168.1.40**

### Firewall Status

✅ No firewall blocking (checked UFW and firewalld)
✅ Port 8000 is open and accessible

### Production vs Development

**Development Mode** (`docker-compose up`):
- Auto-reload on code changes
- Volume mounts for live editing
- Single worker
- Good for: Local development

**Production Mode** (`docker-compose.prod.yml`):
- No auto-reload
- Multiple workers (2)
- Health checks
- Read-only volume mounts
- Good for: Network access from other devices

Use production mode with:
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

Or just use the startup script:
```bash
./docker-start.sh
```

### Troubleshooting

**Can't connect from other device?**

1. **Verify the container is running:**
   ```bash
   docker ps | grep llm-debate
   ```

2. **Check if port 8000 is listening:**
   ```bash
   sudo netstat -tulpn | grep 8000
   ```

3. **Test from the server itself:**
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"healthy","service":"llm-debate-web"}`

4. **Verify your network IP:**
   ```bash
   hostname -I
   ```

5. **Test from another device:**
   ```bash
   # From another machine on the network
   curl http://192.168.1.40:8000/health
   ```

**Still not working?**

Check if another service is using port 8000:
```bash
sudo lsof -i :8000
```

Change the port if needed:
```bash
# Edit docker-compose.prod.yml
ports:
  - "0.0.0.0:8080:8000"  # Use 8080 externally, 8000 internally
```

### Using a Custom Domain

**Option 1: Edit hosts file on client devices**

On the device you want to access from:
```bash
# Linux/Mac: sudo nano /etc/hosts
# Windows: notepad C:\Windows\System32\drivers\etc\hosts

# Add this line:
192.168.1.40  llm-debate.local
```

Then access via: `http://llm-debate.local:8000`

**Option 2: Use mDNS (if available)**

If your network supports mDNS:
```bash
# Access via hostname
http://jolomoadmin-hostname.local:8000
```

### Security Considerations

**For production use, consider:**

1. **Use HTTPS** (add nginx reverse proxy with SSL)
2. **Add authentication** (basic auth or OAuth)
3. **Limit network access** (firewall rules)
4. **Use environment variables** for secrets
5. **Regular updates** (keep Docker images updated)

### Mobile Access

The UI is mobile-responsive! Just open the network URL on your phone:

1. Connect phone to same WiFi network
2. Open browser
3. Go to: `http://192.168.1.40:8000`
4. Enjoy debates on mobile!

### Commands Reference

```bash
# Start (with network info)
./docker-start.sh

# Start manually (production)
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f llm-debate-web

# Stop
docker-compose down

# Restart
docker-compose restart

# Rebuild
docker-compose up --build -d

# Check status
docker-compose ps
```

### API Access

The REST API is also accessible from the network:

```bash
# From another device
curl http://192.168.1.40:8000/health

curl http://192.168.1.40:8000/api/config/modes

curl -X POST http://192.168.1.40:8000/api/debates/start \
  -H "Content-Type: application/json" \
  -d '{"topic": "Test", "mode": "collaborative", "max_rounds": 3}'
```

---

**Your Network URLs:**
- Main UI: http://192.168.1.40:8000
- Health: http://192.168.1.40:8000/health
- API Docs: http://192.168.1.40:8000/docs (FastAPI auto-generated)
