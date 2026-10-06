<?php
// Synthetic parser/runtime check using the target's installed Docker Manager.
$docroot = '/usr/local/emhttp';
$var = ['timeZone' => 'UTC', 'NAME' => 'synthetic'];
$driver = ['bridge' => 'bridge', 'none' => 'none'];
$subnet = ['bridge' => [], 'none' => []];
require "$docroot/plugins/dynamix.docker.manager/include/Helpers.php";
$text = stream_get_contents(STDIN);
$xml = simplexml_load_string($text);
if ($xml === false) exit(1);
$v = xmlToVar($text);
$command = xmlToCommand($text)[0];
$checks = [
    'version2' => (string)$xml['version'] === '2',
    'pinned_image' => $v['Repository'] === 'ghcr.io/h2oking89/abs-audiobookdb:0.1.0',
    'port' => strpos($command, '8080:8080/tcp') !== false,
    'read_only' => strpos($command, '--read-only') !== false,
    'uid' => strpos($command, '--user=99:100') !== false,
    'memory' => strpos($command, '--memory=256m') !== false,
    'nonprivileged' => strpos($command, '--privileged=true') === false,
];
if (in_array(false, $checks, true)) {
    echo json_encode(['checks' => $checks, 'outcome' => 'Fail']), PHP_EOL;
    exit(1);
}
if (count($argv) === 2) {
    $name = 'abs-audiobookdb-template-check-' . bin2hex(random_bytes(4));
    $xml->Name = $name;
    $xml->Repository = $argv[1];
    $xml->Network = 'none';
    $xml->ExtraParams = str_replace('--restart=unless-stopped', '--restart=no', (string)$xml->ExtraParams);
    foreach ($xml->Config as $config) {
        if ((string)$config['Target'] === 'AUDIOBOOKDB_CONTACT') $config[0] = 'operator@example.invalid';
    }
    try {
        exec(xmlToCommand($xml->asXML())[0] . ' >/dev/null 2>&1', $output, $code);
        $checks['create_from_template'] = $code === 0;
        exec('docker start ' . escapeshellarg($name) . ' >/dev/null 2>&1', $output, $code);
        $checks['start'] = $code === 0;
        $healthy = false;
        for ($attempt = 0; $attempt < 30; $attempt++) {
            exec('docker exec ' . escapeshellarg($name) . ' /adapter health >/dev/null 2>&1', $output, $code);
            if ($code === 0) { $healthy = true; break; }
            usleep(200000);
        }
        $checks['health_network_none'] = $healthy;
        exec('docker exec ' . escapeshellarg($name) . ' /adapter version', $version, $code);
        $build = json_decode(implode('', $version), true);
        $checks['version'] = $code === 0 && ($build['version'] ?? '') === '0.1.0';
        exec('docker stop --time 10 ' . escapeshellarg($name) . ' >/dev/null 2>&1', $output, $code);
        $checks['shutdown'] = $code === 0;
    } finally {
        exec('docker rm -f ' . escapeshellarg($name) . ' >/dev/null 2>&1', $output, $code);
        $checks['cleanup'] = $code === 0;
    }
}
$passed = !in_array(false, $checks, true);
echo json_encode(['checks' => $checks, 'outcome' => $passed ? 'Pass' : 'Fail']), PHP_EOL;
exit($passed ? 0 : 1);
