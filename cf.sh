#!/bin/sh

CLOUDFLARE_ZONE_ID="e273eb3bfc6b4e6b91790c962d5e817a"
CLOUDFLARE_RECORD_ID="b5b3d3aaf5f90389bc8341ff58526885"
CLOUDFLARE_API_TOKEN="dfHwH9AncnSoZi6G3CCDS_D4TPa7rj3XLv3J0mXc"

# 获取 IPv6 地址
current_ipv6=$(ifconfig pppoe-wan | grep "240" | awk '{print $3}' | sed 's/\/64//')
# 如果没有获取到 IPv6 地址，则退出脚本
if [ -z "$current_ipv6" ]; then
    echo "未获取到IPv6地址，脚本退出" | logger -t cf_script
    exit 1
fi
# 读取已保存的 IPv6 地址
saved_cf_ipv6=$(cat /usr/cf.txt)
# 比较当前 IPv6 与保存的 IPv6
if [ "$current_ipv6" != "$saved_cf_ipv6" ]; then
    # 更新 Cloudflare 上的 AAAA 记录
    response=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/dns_records/$CLOUDFLARE_RECORD_ID" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data "{\"type\":\"AAAA\",\"name\":\"dns.acyun.us.kg\",\"content\":\"$current_ipv6\",\"ttl\":3600,\"proxied\":false}")
    # 检查是否更新成功
    if echo "$response" | grep -q "\"success\":true"; then
        echo "Cloudflare解析更新成功" | logger -t cf_script
        echo "$current_ipv6" > /usr/cf.txt
    else
        echo "Cloudflare解析更新失败"
    fi
else
    echo "IPv6地址未变化，无需更新"
fi