# Estimated PubSub Costs

## 3 Factors

* Message Raw Throughput
  - Msg/sec * Avg/Size
* Snapshots message backlog
  - ( Msg/sec * Avg/Size ) * weighted Avg Subscription/Topic OR by topic calc
* Subscriptions retained acknowledged messages
  - stored messages

# Links
[https://cloud.google.com/pubsub/pricing#example-subscription-with-retained-acknowledged-messages]
[https://cloud.google.com/skus?currency=USD&filter=pub#sku-pubsub]
[ https://en.wikipedia.org/wiki/Tebibyte]
[https://cloud.google.com/pubsub/docs/reference/rest/v1/Snapshot#:~:text=Its%20exact%20lifetime%20is%20determined,unacked%20message%20in%20the%20subscription)%20.]
[https://docs.google.com/document/d/19ZaR4KiZkWzR2xshvAgs_Fof05NAqL8596KokmjFAPY/edit#] 
