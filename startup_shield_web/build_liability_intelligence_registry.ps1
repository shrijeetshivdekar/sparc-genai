param(
  [string]$SourceDocx = "_tmp_liability.docx",
  [string]$OutputJson = "startup_shield_web/liability_intelligence_registry.json"
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.IO.Compression.FileSystem

function Get-NodeText {
  param(
    [Parameter(Mandatory=$true)] $Node,
    [Parameter(Mandatory=$true)] $Ns
  )

  if ($Node.LocalName -eq 'p') {
    return (($Node.SelectNodes('.//w:t', $Ns) | ForEach-Object { $_.'#text' }) -join '').Trim()
  }

  if ($Node.LocalName -eq 'tbl') {
    $rows = @()
    foreach ($tr in $Node.SelectNodes('./w:tr', $Ns)) {
      $cells = @()
      foreach ($tc in $tr.SelectNodes('./w:tc', $Ns)) {
        $cellText = (($tc.SelectNodes('.//w:t', $Ns) | ForEach-Object { $_.'#text' }) -join '').Trim()
        $cells += $cellText
      }
      $rows += ,$cells
    }
    return $rows
  }

  return $null
}

function Get-ParagraphStyle {
  param(
    [Parameter(Mandatory=$true)] $Node,
    [Parameter(Mandatory=$true)] $Ns
  )

  $pPr = $Node.SelectSingleNode('./w:pPr', $Ns)
  if (-not $pPr) { return $null }
  $sn = $pPr.SelectSingleNode('./w:pStyle', $Ns)
  if (-not $sn) { return $null }
  return $sn.GetAttribute('val', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
}

function Get-HeadingLevel {
  param(
    [Parameter(Mandatory=$true)] [string] $Style
  )

  if ($Style -eq 'Title') { return 0 }
  if ($Style -match '^Heading([1-4])$') { return [int]$Matches[1] }
  return $null
}

function New-TreeNode {
  param(
    [Parameter(Mandatory=$true)] [int]$Level,
    [Parameter(Mandatory=$true)] [string]$Title
  )

  return [pscustomobject]@{
    level = $Level
    title = $Title
    content = New-Object 'System.Collections.Generic.List[object]'
    children = New-Object 'System.Collections.Generic.List[object]'
  }
}

function Get-ProductKey {
  param([string]$Title)

  if ($null -eq $Title) { $Title = "" }
  $t = $Title.ToLowerInvariant()
  switch -Regex ($t) {
    'cgl' { return 'comprehensive_general_liability' }
    'public liability' { return 'public_liability' }
    'product liability' { return 'product_liability' }
    'healthcare and medical professional liability' { return 'healthcare_pi' }
    'financial services / institutions professional indemnity' { return 'financial_services_pi' }
    'engineers' { return 'professional_indemnity_engineers' }
    '^e&o' { return 'technology_eo' }
    'employment practices liability' { return 'employment_practices' }
    'cyber liability insurance' { return 'cyber_liability' }
    'professional indemnity' { return 'professional_indemnity' }
    default {
      $slug = ($Title -replace '[^a-zA-Z0-9]+','_').Trim('_').ToLowerInvariant()
      return $slug
    }
  }
}

$sourcePath = (Resolve-Path $SourceDocx).Path
$zip = [System.IO.Compression.ZipFile]::OpenRead($sourcePath)
try {
  $entry = $zip.GetEntry('word/document.xml')
  if (-not $entry) { throw "word/document.xml not found in $sourcePath" }
  $reader = New-Object System.IO.StreamReader($entry.Open())
  try {
    $xml = [xml]$reader.ReadToEnd()
  } finally {
    $reader.Dispose()
  }

  $ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
  $ns.AddNamespace('w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')

  $body = $xml.SelectSingleNode('//w:body', $ns)
  if (-not $body) { throw "Document body not found." }

  $products = New-Object 'System.Collections.Generic.List[object]'
  $current = $null
  $stack = New-Object 'System.Collections.Generic.List[object]'

  foreach ($node in $body.ChildNodes) {
    if ($node.NodeType -ne [System.Xml.XmlNodeType]::Element) { continue }

    if ($node.LocalName -eq 'p') {
      $text = Get-NodeText -Node $node -Ns $ns
      if (-not $text) { continue }
      $style = Get-ParagraphStyle -Node $node -Ns $ns
      $level = if ($style) { Get-HeadingLevel -Style $style } else { $null }

      if ($level -eq 0) {
        if ($current) {
          $products.Add($current)
        }
        $current = [pscustomobject]@{
          key = Get-ProductKey -Title $text
          title = $text
          root = New-TreeNode -Level 0 -Title $text
        }
        $stack.Clear()
        continue
      }

      if (-not $current) { continue }

      if ($null -ne $level) {
        while ($stack.Count -gt 0 -and $stack[$stack.Count - 1].level -ge $level) {
          $stack.RemoveAt($stack.Count - 1)
        }

        $newNode = New-TreeNode -Level $level -Title $text
        if ($stack.Count -eq 0) {
          $current.root.children.Add($newNode)
        } else {
          $stack[$stack.Count - 1].children.Add($newNode)
        }
        $stack.Add($newNode)
        continue
      }

      $target = if ($stack.Count -gt 0) { $stack[$stack.Count - 1] } else { $current.root }
      $target.content.Add([pscustomobject]@{ type = 'paragraph'; text = $text })
      continue
    }

    if ($node.LocalName -eq 'tbl' -and $current) {
      $rows = Get-NodeText -Node $node -Ns $ns
      $target = if ($stack.Count -gt 0) { $stack[$stack.Count - 1] } else { $current.root }
      $target.content.Add([pscustomobject]@{ type = 'table'; rows = $rows })
    }
  }

  if ($current) {
    $products.Add($current)
  }

  $registry = [pscustomobject]@{
    generated_at = (Get-Date).ToString('s')
    source_docx = [System.IO.Path]::GetFileName($sourcePath)
    products = $products
  }

  $json = $registry | ConvertTo-Json -Depth 20
  Set-Content -LiteralPath $OutputJson -Value $json -Encoding UTF8
  Write-Output ("Wrote " + (Resolve-Path $OutputJson).Path)
} finally {
  $zip.Dispose()
}
