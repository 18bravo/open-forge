{{/*
Expand the name of the chart.
*/}}
{{- define "open-forge.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "open-forge.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "open-forge.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "open-forge.labels" -}}
helm.sh/chart: {{ include "open-forge.chart" . }}
{{ include "open-forge.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: open-forge
{{- if .Values.commonLabels }}
{{ toYaml .Values.commonLabels }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "open-forge.selectorLabels" -}}
app.kubernetes.io/name: {{ include "open-forge.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
API labels
*/}}
{{- define "open-forge.api.labels" -}}
{{ include "open-forge.labels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
API selector labels
*/}}
{{- define "open-forge.api.selectorLabels" -}}
{{ include "open-forge.selectorLabels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
UI labels
*/}}
{{- define "open-forge.ui.labels" -}}
{{ include "open-forge.labels" . }}
app.kubernetes.io/component: ui
{{- end }}

{{/*
UI selector labels
*/}}
{{- define "open-forge.ui.selectorLabels" -}}
{{ include "open-forge.selectorLabels" . }}
app.kubernetes.io/component: ui
{{- end }}

{{/*
Dagster labels
*/}}
{{- define "open-forge.dagster.labels" -}}
{{ include "open-forge.labels" . }}
app.kubernetes.io/component: dagster
{{- end }}

{{/*
Langflow labels
*/}}
{{- define "open-forge.langflow.labels" -}}
{{ include "open-forge.labels" . }}
app.kubernetes.io/component: langflow
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "open-forge.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "open-forge.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the API service account
*/}}
{{- define "open-forge.api.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- printf "%s-api" (include "open-forge.fullname" .) }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the UI service account
*/}}
{{- define "open-forge.ui.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- printf "%s-ui" (include "open-forge.fullname" .) }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Return the API image name
*/}}
{{- define "open-forge.api.image" -}}
{{- $tag := default .Chart.AppVersion .Values.api.image.tag -}}
{{- printf "%s:%s" .Values.api.image.repository $tag }}
{{- end }}

{{/*
Return the UI image name
*/}}
{{- define "open-forge.ui.image" -}}
{{- $tag := default .Chart.AppVersion .Values.ui.image.tag -}}
{{- printf "%s:%s" .Values.ui.image.repository $tag }}
{{- end }}

{{/*
Return the Dagster image name
*/}}
{{- define "open-forge.dagster.image" -}}
{{- $tag := default .Chart.AppVersion .Values.dagster.webserver.image.tag -}}
{{- printf "%s:%s" .Values.dagster.webserver.image.repository $tag }}
{{- end }}

{{/*
Return the Langflow image name
*/}}
{{- define "open-forge.langflow.image" -}}
{{- printf "%s:%s" .Values.langflow.image.repository .Values.langflow.image.tag }}
{{- end }}

{{/*
Return the secrets name
*/}}
{{- define "open-forge.secretsName" -}}
{{- if .Values.secrets.existingSecret }}
{{- .Values.secrets.existingSecret }}
{{- else }}
{{- printf "%s-secrets" (include "open-forge.fullname" .) }}
{{- end }}
{{- end }}

{{/*
Return the configmap name
*/}}
{{- define "open-forge.configMapName" -}}
{{- printf "%s-config" (include "open-forge.fullname" .) }}
{{- end }}

{{/*
Return the PostgreSQL hostname
*/}}
{{- define "open-forge.postgresql.host" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "%s-postgresql" .Release.Name }}
{{- else }}
{{- .Values.externalDatabase.host }}
{{- end }}
{{- end }}

{{/*
Return the Redis hostname
*/}}
{{- define "open-forge.redis.host" -}}
{{- if .Values.redis.enabled }}
{{- printf "%s-redis-master" .Release.Name }}
{{- else }}
{{- .Values.externalRedis.host }}
{{- end }}
{{- end }}

{{/*
Return the MinIO hostname
*/}}
{{- define "open-forge.minio.host" -}}
{{- if .Values.minio.enabled }}
{{- printf "%s-minio" .Release.Name }}
{{- else }}
{{- .Values.externalMinio.host }}
{{- end }}
{{- end }}

{{/*
Create pod security context
*/}}
{{- define "open-forge.podSecurityContext" -}}
{{- toYaml .Values.podSecurityContext }}
{{- end }}

{{/*
Create container security context
*/}}
{{- define "open-forge.securityContext" -}}
{{- toYaml .Values.securityContext }}
{{- end }}

{{/*
Common annotations for all resources
*/}}
{{- define "open-forge.annotations" -}}
{{- if .Values.commonAnnotations }}
{{ toYaml .Values.commonAnnotations }}
{{- end }}
{{- end }}

{{/*
Render probe configuration
*/}}
{{- define "open-forge.probe" -}}
{{- if .httpGet }}
httpGet:
  path: {{ .httpGet.path }}
  port: {{ .httpGet.port }}
{{- end }}
{{- if .exec }}
exec:
  command:
    {{- toYaml .exec.command | nindent 4 }}
{{- end }}
initialDelaySeconds: {{ default 30 .initialDelaySeconds }}
periodSeconds: {{ default 10 .periodSeconds }}
timeoutSeconds: {{ default 5 .timeoutSeconds }}
failureThreshold: {{ default 3 .failureThreshold }}
successThreshold: {{ default 1 .successThreshold }}
{{- end }}
