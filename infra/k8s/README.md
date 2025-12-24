# Kubernetes Manifests

Bu dizin Kubernetes deployment manifests içerir.

## Planlanan İçerik

```
infra/k8s/
├── README.md           # Bu dosya
├── namespace.yaml      # Namespace tanımı
├── deployment.yaml     # Deployment
├── service.yaml        # Service (ClusterIP/LoadBalancer)
├── configmap.yaml      # ConfigMap
├── secrets.yaml        # Secrets (template)
├── ingress.yaml        # Ingress (nginx)
├── hpa.yaml            # Horizontal Pod Autoscaler
└── pdb.yaml            # Pod Disruption Budget
```

## Örnek Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: globalmain-web
  namespace: globalmain
spec:
  replicas: 3
  selector:
    matchLabels:
      app: globalmain-web
  template:
    metadata:
      labels:
        app: globalmain-web
    spec:
      containers:
      - name: web
        image: globalmain:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: globalmain-config
        - secretRef:
            name: globalmain-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /live/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Örnek Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: globalmain-web
  namespace: globalmain
spec:
  selector:
    app: globalmain-web
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

## Kullanım

```bash
# Namespace oluştur
kubectl apply -f namespace.yaml

# Tüm kaynakları deploy et
kubectl apply -f .

# Durumu kontrol et
kubectl get pods -n globalmain
kubectl get svc -n globalmain
```

## TODO

- [ ] Namespace manifest
- [ ] Deployment manifest
- [ ] Service manifest
- [ ] ConfigMap (env variables)
- [ ] Secrets template
- [ ] Ingress (nginx-ingress)
- [ ] HPA
- [ ] PDB
- [ ] Helm chart (optional)

