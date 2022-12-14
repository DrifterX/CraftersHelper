$firstPass = Get-Content C:\Users\NHolm\Downloads\Item.csv
$headers = $firstPass[1].Split(",")
for($i = 0; $i -lt $headers.Count; $i++) {
    if($headers[$i] -like "") {
        $headers[$i] = $i
    }
}
$headers[0] = "ID"
$firstCsv = Import-Csv "C:\Users\NHolm\Downloads\item.csv" -Header $headers

$firstHashArray = for($i = 3; $i -lt $firstCsv.Count; $i++) {$firstCsv[$i]}

$noUntradable = $firstHashArray | Where-Object {$_.isUntradable -like "FALSE"}
$noUnnamed = $noUntradable | Where-Object {$_.Name -notlike ""}
$noCurrency = $noUnnamed | Where-Object {$_.ItemSortCategory -ne 3}

$noDeliverables = $noCurrency | Where-Object {$_.ItemSortCategory -lt 31 -or $_.ItemSortCategory -gt 36}
$noDeliverables = $noDeliverables | Where-Object {$_.ItemSortCategory -ne 69 -and $_.ItemSortCategory -ne 72}


$noDeliverables | Export-Csv "G:\OneDrive\MyDashApp\src\item.csv" -NoTypeInformation 


$servers = Invoke-RestMethod -Method GET -Uri "https://universalis.app/api/v2/worlds"