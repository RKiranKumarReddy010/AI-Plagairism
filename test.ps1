$apiKey = "AIzaSyB9ouZqk4pxpx9sIyleteZR1O8vTDasT3c"
$body = @{
    text = 'the tortured Prince of Denmark delivers his famous "To be, or not to be" soliloquy, a deeply philosophical contemplation on life, death, and human suffering. Faced with the devastating burdens of his father''s murder and his mother''s hasty remarriage, Hamlet weighs the agonizing pain of remaining alive ("to be") against the peaceful release of suicide ("not to be"). He compares death to a sleep that might finally end the "heartache" of existence, yet he hesitates because no one knows what nightmares might exist in the afterlife—the "undiscovered country" from which no traveller returns. Ultimately, Hamlet concludes that this paralyzing fear of the unknown turns people into cowards, draining them of the resolve needed to take action.'
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/usr_456/detect_ai" -Method POST -ContentType "application/json" -Body $body -Headers @{"Authorization"=$apiKey}
$response.Content
