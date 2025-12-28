# deploy_gis.ps1
# نص برمجى لتسهيل عملية الرفع على جوجل كلاود

$PROJECT_ID = "el-massa-consult"
$REGION = "europe-west1"

Write-Host "1. تجهيز مجلد البيانات..." -ForegroundColor Cyan
if (Test-Path "gis_assets") { Remove-Item -Recurse -Force "gis_assets" }
New-Item -ItemType Directory -Path "gis_assets"
Copy-Item -Path "../assets/gis/*" -Destination "gis_assets/" -Recurse

Write-Host "2. البدء في عملية الرفع إلى Cloud Run..." -ForegroundColor Cyan
gcloud run deploy gis-service `
    --source . `
    --project $PROJECT_ID `
    --region $REGION `
    --allow-unauthenticated `
    --platform managed

Write-Host "`nتم الانتهاء! يرجى نسخ الرابط الذي سيظهر أعلاه وتزويدي به." -ForegroundColor Green
