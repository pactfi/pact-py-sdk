Search.setIndex({docnames:["docs/source/modules","docs/source/pactsdk","examples/add_liquidity","examples/composing_transactions","examples/get_pool_state","examples/index","examples/swap","examples/zap","index","pactsdk/api","pactsdk/asset","pactsdk/client","pactsdk/constant_product_calculator","pactsdk/exceptions","pactsdk/index","pactsdk/pool","pactsdk/pool_calculator","pactsdk/pool_state","pactsdk/stableswap_calculator","pactsdk/swap","pactsdk/transaction_group","pactsdk/zap"],envversion:{"sphinx.domains.c":2,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":5,"sphinx.domains.index":1,"sphinx.domains.javascript":2,"sphinx.domains.math":2,"sphinx.domains.python":3,"sphinx.domains.rst":2,"sphinx.domains.std":2,sphinx:56},filenames:["docs/source/modules.rst","docs/source/pactsdk.rst","examples/add_liquidity.rst","examples/composing_transactions.rst","examples/get_pool_state.rst","examples/index.rst","examples/swap.rst","examples/zap.rst","index.rst","pactsdk/api.rst","pactsdk/asset.rst","pactsdk/client.rst","pactsdk/constant_product_calculator.rst","pactsdk/exceptions.rst","pactsdk/index.rst","pactsdk/pool.rst","pactsdk/pool_calculator.rst","pactsdk/pool_state.rst","pactsdk/stableswap_calculator.rst","pactsdk/swap.rst","pactsdk/transaction_group.rst","pactsdk/zap.rst"],objects:{"":[[1,0,0,"-","pactsdk"]],"pactsdk.api":[[9,1,1,"","ApiAsset"],[9,1,1,"","ApiListPoolsResponse"],[9,1,1,"","ApiPool"],[9,1,1,"","ListPoolsParams"],[9,3,1,"","list_pools"]],"pactsdk.api.ApiAsset":[[9,2,1,"","algoid"],[9,2,1,"","decimals"],[9,2,1,"","id"],[9,2,1,"","is_liquidity_token"],[9,2,1,"","is_verified"],[9,2,1,"","name"],[9,2,1,"","total_amount"],[9,2,1,"","tvl_usd"],[9,2,1,"","unit_name"],[9,2,1,"","volume_24h"],[9,2,1,"","volume_7d"]],"pactsdk.api.ApiListPoolsResponse":[[9,2,1,"","count"],[9,2,1,"","limit"],[9,2,1,"","offset"],[9,2,1,"","results"]],"pactsdk.api.ApiPool":[[9,2,1,"","address"],[9,2,1,"","appid"],[9,2,1,"","apr_7d"],[9,2,1,"","confirmed_round"],[9,2,1,"","creator"],[9,2,1,"","fee_amount_24h"],[9,2,1,"","fee_amount_7d"],[9,2,1,"","fee_usd_24h"],[9,2,1,"","fee_usd_7d"],[9,2,1,"","id"],[9,2,1,"","is_verified"],[9,2,1,"","pool_asset"],[9,2,1,"","primary_asset"],[9,2,1,"","secondary_asset"],[9,2,1,"","tvl_usd"],[9,2,1,"","volume_24h"],[9,2,1,"","volume_7d"]],"pactsdk.api.ListPoolsParams":[[9,2,1,"","creator"],[9,2,1,"","is_verified"],[9,2,1,"","limit"],[9,2,1,"","offset"],[9,2,1,"","primary_asset__algoid"],[9,2,1,"","primary_asset__name"],[9,2,1,"","primary_asset__unit_name"],[9,2,1,"","secondary_asset__algoid"],[9,2,1,"","secondary_asset__name"],[9,2,1,"","secondary_asset__unit_name"]],"pactsdk.asset":[[10,4,1,"","ASSETS_CACHE"],[10,1,1,"","Asset"],[10,3,1,"","fetch_asset_by_index"]],"pactsdk.asset.Asset":[[10,5,1,"","__eq__"],[10,2,1,"","algod"],[10,5,1,"","build_opt_in_tx"],[10,2,1,"","decimals"],[10,5,1,"","get_holding"],[10,2,1,"","index"],[10,5,1,"","is_opted_in"],[10,2,1,"","name"],[10,5,1,"","prepare_opt_in_tx"],[10,6,1,"","ratio"],[10,2,1,"","unit_name"]],"pactsdk.client":[[11,1,1,"","PactClient"]],"pactsdk.client.PactClient":[[11,5,1,"","__init__"],[11,2,1,"","algod"],[11,5,1,"","fetch_asset"],[11,5,1,"","fetch_pool_by_id"],[11,5,1,"","fetch_pools_by_assets"],[11,5,1,"","list_pools"],[11,2,1,"","pact_api_url"]],"pactsdk.constant_product_calculator":[[12,1,1,"","ConstantProductCalculator"],[12,1,1,"","ConstantProductParams"],[12,3,1,"","get_constant_product_minted_liquidity_tokens"],[12,3,1,"","get_swap_amount_deposited"],[12,3,1,"","get_swap_gross_amount_received"]],"pactsdk.constant_product_calculator.ConstantProductCalculator":[[12,5,1,"","get_minted_liquidity_tokens"],[12,5,1,"","get_price"],[12,5,1,"","get_swap_amount_deposited"],[12,5,1,"","get_swap_gross_amount_received"]],"pactsdk.constant_product_calculator.ConstantProductParams":[[12,2,1,"","fee_bps"],[12,2,1,"","pact_fee_bps"]],"pactsdk.exceptions":[[13,7,1,"","PactSdkError"]],"pactsdk.pool":[[15,4,1,"","OperationType"],[15,1,1,"","Pool"],[15,3,1,"","fetch_app_global_state"],[15,3,1,"","fetch_pool_by_id"],[15,3,1,"","fetch_pools_by_assets"],[15,3,1,"","get_app_ids_from_assets"]],"pactsdk.pool.Pool":[[15,2,1,"","algod"],[15,2,1,"","app_id"],[15,5,1,"","build_add_liquidity_txs"],[15,5,1,"","build_raw_add_liquidity_txs"],[15,5,1,"","build_remove_liquidity_txs"],[15,5,1,"","build_swap_txs"],[15,5,1,"","build_zap_txs"],[15,2,1,"","fee_bps"],[15,5,1,"","get_escrow_address"],[15,5,1,"","get_other_asset"],[15,2,1,"","internal_state"],[15,5,1,"","is_asset_in_the_pool"],[15,2,1,"","liquidity_asset"],[15,5,1,"","parse_internal_state"],[15,2,1,"","pool_type"],[15,5,1,"","prepare_add_liquidity"],[15,5,1,"","prepare_add_liquidity_tx_group"],[15,5,1,"","prepare_remove_liquidity_tx_group"],[15,5,1,"","prepare_swap"],[15,5,1,"","prepare_swap_tx_group"],[15,5,1,"","prepare_zap"],[15,5,1,"","prepare_zap_tx_group"],[15,2,1,"","primary_asset"],[15,2,1,"","secondary_asset"],[15,5,1,"","update_state"],[15,2,1,"","version"]],"pactsdk.pool_calculator":[[16,1,1,"","PoolCalculator"],[16,1,1,"","SwapCalculator"]],"pactsdk.pool_calculator.PoolCalculator":[[16,5,1,"","amount_deposited_to_net_amount_received"],[16,5,1,"","get_asset_price_after_liq_change"],[16,5,1,"","get_fee"],[16,5,1,"","get_fee_from_gross_amount"],[16,5,1,"","get_fee_from_net_amount"],[16,5,1,"","get_liquidities"],[16,5,1,"","get_minimum_amount_received"],[16,5,1,"","get_price_impact_pct"],[16,5,1,"","get_swap_price"],[16,6,1,"","is_empty"],[16,5,1,"","net_amount_received_to_amount_deposited"],[16,6,1,"","primary_asset_amount"],[16,6,1,"","primary_asset_amount_decimal"],[16,6,1,"","primary_asset_price"],[16,6,1,"","secondary_asset_amount"],[16,6,1,"","secondary_asset_amount_decimal"],[16,6,1,"","secondary_asset_price"]],"pactsdk.pool_calculator.SwapCalculator":[[16,5,1,"","get_minted_liquidity_tokens"],[16,5,1,"","get_price"],[16,5,1,"","get_swap_amount_deposited"],[16,5,1,"","get_swap_gross_amount_received"],[16,2,1,"","pool"]],"pactsdk.pool_state":[[17,1,1,"","AppInternalState"],[17,1,1,"","PoolState"],[17,3,1,"","get_pool_type_from_internal_state"],[17,3,1,"","parse_global_pool_state"],[17,3,1,"","parse_state"]],"pactsdk.pool_state.AppInternalState":[[17,2,1,"","A"],[17,2,1,"","ADMIN"],[17,2,1,"","ASSET_A"],[17,2,1,"","ASSET_B"],[17,2,1,"","B"],[17,2,1,"","CONTRACT_NAME"],[17,2,1,"","FEE_BPS"],[17,2,1,"","FUTURE_A"],[17,2,1,"","FUTURE_ADMIN"],[17,2,1,"","FUTURE_A_TIME"],[17,2,1,"","INITIAL_A"],[17,2,1,"","INITIAL_A_TIME"],[17,2,1,"","L"],[17,2,1,"","LTID"],[17,2,1,"","PACT_FEE_BPS"],[17,2,1,"","PRECISION"],[17,2,1,"","PRIMARY_FEES"],[17,2,1,"","SECONDARY_FEES"],[17,2,1,"","TREASURY"],[17,2,1,"","VERSION"]],"pactsdk.pool_state.PoolState":[[17,2,1,"","primary_asset_price"],[17,2,1,"","secondary_asset_price"],[17,2,1,"","total_liquidity"],[17,2,1,"","total_primary"],[17,2,1,"","total_secondary"]],"pactsdk.stableswap_calculator":[[18,7,1,"","ConvergenceError"],[18,1,1,"","StableswapCalculator"],[18,1,1,"","StableswapParams"],[18,3,1,"","get_add_liquidity_bonus_pct"],[18,3,1,"","get_add_liquidity_fees"],[18,3,1,"","get_amplifier"],[18,3,1,"","get_invariant"],[18,3,1,"","get_new_liq"],[18,3,1,"","get_stableswap_minted_liquidity_tokens"],[18,3,1,"","get_swap_amount_deposited"],[18,3,1,"","get_swap_gross_amount_received"],[18,3,1,"","get_tx_fee"]],"pactsdk.stableswap_calculator.StableswapCalculator":[[18,5,1,"","_get_price"],[18,5,1,"","get_amplifier"],[18,5,1,"","get_minted_liquidity_tokens"],[18,5,1,"","get_price"],[18,5,1,"","get_swap_amount_deposited"],[18,5,1,"","get_swap_gross_amount_received"],[18,2,1,"","mint_tokens_invariant_iterations"],[18,6,1,"","stableswap_params"],[18,2,1,"","swap_invariant_iterations"]],"pactsdk.stableswap_calculator.StableswapParams":[[18,2,1,"","fee_bps"],[18,2,1,"","future_a"],[18,2,1,"","future_a_time"],[18,2,1,"","initial_a"],[18,2,1,"","initial_a_time"],[18,2,1,"","pact_fee_bps"],[18,2,1,"","precision"]],"pactsdk.swap":[[19,1,1,"","Swap"],[19,1,1,"","SwapEffect"]],"pactsdk.swap.Swap":[[19,2,1,"","amount"],[19,2,1,"","asset_deposited"],[19,2,1,"","asset_received"],[19,2,1,"","effect"],[19,2,1,"","pool"],[19,5,1,"","prepare_tx_group"],[19,2,1,"","slippage_pct"],[19,2,1,"","swap_for_exact"]],"pactsdk.swap.SwapEffect":[[19,2,1,"","amount_deposited"],[19,2,1,"","amount_received"],[19,2,1,"","amplifier"],[19,2,1,"","fee"],[19,2,1,"","minimum_amount_received"],[19,2,1,"","price"],[19,2,1,"","primary_asset_price_after_swap"],[19,2,1,"","primary_asset_price_change_pct"],[19,2,1,"","secondary_asset_price_after_swap"],[19,2,1,"","secondary_asset_price_change_pct"],[19,2,1,"","tx_fee"]],"pactsdk.transaction_group":[[20,1,1,"","TransactionGroup"]],"pactsdk.transaction_group.TransactionGroup":[[20,5,1,"","__init__"],[20,6,1,"","group_id"],[20,5,1,"","sign"],[20,2,1,"","transactions"]],"pactsdk.zap":[[21,1,1,"","Zap"],[21,1,1,"","ZapParams"],[21,3,1,"","get_constant_product_zap_params"],[21,3,1,"","get_secondary_added_liquidity_from_zapping"],[21,3,1,"","get_swap_amount_deposited_from_zapping"]],"pactsdk.zap.Zap":[[21,2,1,"","amount"],[21,2,1,"","asset"],[21,5,1,"","get_zap_params"],[21,2,1,"","liquidity_addition"],[21,2,1,"","params"],[21,2,1,"","pool"],[21,5,1,"","prepare_add_liq"],[21,5,1,"","prepare_tx_group"],[21,2,1,"","slippage_pct"],[21,2,1,"","swap"]],"pactsdk.zap.ZapParams":[[21,2,1,"","primary_add_liq"],[21,2,1,"","secondary_add_liq"],[21,2,1,"","swap_deposited"]],pactsdk:[[9,0,0,"-","api"],[10,0,0,"-","asset"],[11,0,0,"-","client"],[12,0,0,"-","constant_product_calculator"],[13,0,0,"-","exceptions"],[15,0,0,"-","pool"],[16,0,0,"-","pool_calculator"],[17,0,0,"-","pool_state"],[18,0,0,"-","stableswap_calculator"],[19,0,0,"-","swap"],[20,0,0,"-","transaction_group"],[21,0,0,"-","zap"]]},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","attribute","Python attribute"],"3":["py","function","Python function"],"4":["py","data","Python data"],"5":["py","method","Python method"],"6":["py","property","Python property"],"7":["py","exception","Python exception"]},objtypes:{"0":"py:module","1":"py:class","2":"py:attribute","3":"py:function","4":"py:data","5":"py:method","6":"py:property","7":"py:exception"},terms:{"0":[1,2,4,6,7,8,11,15,18,20],"091142966447585":8,"1":8,"10":[1,8,15,18],"1000":[1,15],"100_000":[3,6,7,8],"12345678":[1,11],"1255182523659604":8,"143598":8,"146529":8,"19":8,"1_000_000":[2,8],"2":[1,6,7,8,15],"200000":8,"200_000":[3,8],"3":[1,15],"30":[1,15],"31":8,"31566704":[2,4,6,7],"441":8,"456321":8,"46":8,"500_000":2,"50_000":8,"549580645715963":8,"6":[1,18],"6081680080300244":8,"620995314":3,"64":[1,15],"6442824791774173":8,"73485":8,"849972":8,"8884795940873393":8,"8949213":8,"900000":8,"956659":8,"9843123":8,"byte":[1,17],"case":[1,18],"class":[1,9,10,11,12,15,16,17,18,19,20,21],"default":[1,8,15],"do":[1,6,7,19],"float":[1,10,12,15,16,17,18,19,21],"function":[1,9,10,15,16,17,18],"import":[1,2,3,4,6,7,8,11],"int":[1,9,10,11,12,15,16,17,18,19,21],"new":[1,15,16],"return":[1,8,9,10,11,12,15,16,17,18,19,20,21],"true":[1,10,15,16,18,19],"try":[1,18],A:[1,10,11,15,16,17,18,19,20,21],By:8,For:[1,15,21],If:[1,11,15,19,20],In:[1,10,15,18],It:[1,8,11,19],One:[1,15],The:[1,8,9,10,11,13,15,16,17,18,19,20,21],There:[1,8,15],To:[1,18],__eq__:[1,10],__init__:[1,11,20],__version__:8,_get_pric:[1,18],_tx:8,_tx_group:8,abl:[1,10],about:[1,9,10,11,16],abov:[1,15],accept:[1,15,16],accord:[1,11],account:[1,2,3,6,7,8,10,15,19,21],across:[1,11],actual:[1,10],ad:[1,15,16,18,21],add:[1,3,5,8,15,16,21],add_liq_tx_group:[2,8],add_liquid:[1,21],add_liquidity_tx:3,added_liq_a:[1,12,16,18],added_liq_b:[1,12,16,18],added_primari:[1,12,18],added_secondari:[1,12,18],addit:[1,15,18,21],addliq:[1,15],address:[1,2,3,6,7,8,9,10,15,19,21],address_from_private_kei:[2,3,6,7,8],admin:[1,17],after:[1,8,16],algo:[1,2,3,4,6,7,8,11,15],algod:[1,2,3,4,6,7,8,10,11,15],algodcli:[1,2,3,4,6,7,8,10,11,15],algodhttperror:[1,11],algoid:[1,9],algorand:[1,8,10,11,15,17,18,20],algosdk:[1,2,3,4,6,7,8,10,11,15,17,20],alia:[1,15],all:[1,8,9,15,18,20,21],allow:[1,10,15,19,21],alreadi:[1,10,16],also:[1,8,10],amm:[1,15,17],amount:[1,6,7,8,10,15,16,18,19,21],amount_deposit:[1,8,12,16,18,19],amount_deposited_to_net_amount_receiv:[1,16],amount_receiv:[1,8,16,19],amountdeposit:[1,16],amountreceiv:[1,16],amp:[1,18],amplifi:[1,18,19],an:[1,10,11,12,15,18,19,20],ani:[1,15,17],api:[0,8,11,14,15],apiasset:[1,9],apilistpoolsrespons:[1,9,11],apipool:[1,9],app:[1,8,11,15,18],app_id:[1,11,15],appid:[1,9],appinternalst:[1,15,17],applic:[1,11,15],apr_7d:[1,9],ar:[1,8,9,10,11,15,16,19,21],arg:[1,16],arrai:[1,16,20],asa:[1,10,11],ask:8,assertionerror:[1,15],asset:[0,3,6,7,8,9,11,14,15,16,19,21],asset_a:[1,15,17],asset_b:[1,15,17],asset_deposit:[1,16,19],asset_index:[1,11],asset_receiv:[1,19],assets_cach:[1,10],assettransfertxn:[1,10],assign:[1,20],atom:3,autom:8,automat:[1,10],avail:[1,18],b:[1,15,17],base64:[1,17,20],base:[1,9,10,11,12,13,15,16,17,18,19,20,21],basi:[1,15],basic:[1,9,10,15,19],befor:[1,8,10],behind:[1,12,18],between:[1,10,15],blockchain:[1,11,15],bool:[1,9,10,15,16,19],both:[1,15,18,21],box:[1,21],build:[1,15],build_:8,build_add_liquidity_tx:[1,3,15],build_opt_in_tx:[1,10],build_raw_add_liquidity_tx:[1,15],build_remove_liquidity_tx:[1,15],build_swap_tx:[1,8,15],build_zap_tx:[1,15],buildaddliquiditytx:[1,15],buildswaptx:[1,15],built:[1,15],burn:[1,15],c:8,cach:[1,10],calcul:[1,16,18,19],call:[1,9,10,11,15,18],can:[1,8,9,15],caution:8,cd:8,certain:[1,16],chain:8,chang:[1,16],check:[1,8,10,15,16],circumst:[1,15],client:[0,8,10,14,15,19],clone:8,com:8,commit:[1,19,21],compar:[1,10],compos:5,comput:[1,19],confirmed_round:[1,9],constant:[1,12,15,21],constant_product:[1,15,17],constant_product_calcul:[0,8,14],constantproductcalcul:[1,12],constantproductparam:[1,12],construct:[1,15,19],constructor:[1,11],contain:[1,9,16],content:0,contract:[1,8,11,15,16,17,18,19],contract_nam:[1,17],conveni:[1,8,11,20],convergenceerror:[1,18],convert:[1,10,16,17],correspond:[1,15],count:[1,8,9],cover:8,creat:[1,8,10,15,18,19,20,21],creation:[1,15],creator:[1,9],current:[1,8,10,16],custom:8,d:8,data:[1,9,10,11,15,16,17],deal:[1,10],decentr:8,decim:[1,9,10,16],decod:[1,17],def:8,depend:[1,17,19],deposit:[1,15,16,19],describ:[1,10],detail:[1,9,10,15,19],dict:[1,9,10,17],dictionari:[1,10,17],differ:[1,8,15,16,18],direct:8,directli:[1,8,11],dist:8,docker:8,document:8,doe:[1,11],don:[1,10,15,19,21],due:[1,20,21],dure:[1,21],e:[1,8,10,15,20],each:[1,8,18,20],easier:[1,20],effect:[1,8,19],either:[1,16,17,19],empti:[1,11,15,16,18,20],enabl:[1,15],encod:[1,17,20],enhanc:8,ensur:[1,15],entri:[1,11],equal:[1,10,15],error:[1,11],escrow:[1,15],everi:[1,10],exact:[1,16,19],exampl:[1,2,3,4,6,7,8,11],except:[0,8,14,18],exchang:[1,16,19,21],execut:[1,15,19,21],exist:[1,11],experi:8,explicit:8,explicitli:[1,10],expos:[1,11,15],express:[1,15],extend:8,extra:[1,18],extra_margin:[1,18],extract:[1,10],f:[2,3,4,6,7],fail:[1,15,18],failur:[1,20],fals:[1,10,15,16,19],featur:[1,15],fee:[1,8,15,16,18,19],fee_amount_24h:[1,9],fee_amount_7d:[1,9],fee_bp:[1,8,12,15,16,17,18,21],fee_usd_24h:[1,9],fee_usd_7d:[1,9],fetch:[1,4,8,10,11,15],fetch_app_global_st:[1,15],fetch_asset:[1,2,4,6,7,8,10,11],fetch_asset_by_index:[1,10],fetch_pool_by_id:[1,3,8,10,11,15],fetch_pools_by_asset:[1,2,4,6,7,8,11,15],fi:[1,8,11],filter:8,find:[1,9,11,15],first:[1,11],flag:[1,15],formula:[1,15,16],found:8,fresh:8,friendli:[1,17],from:[1,2,3,4,6,7,8,9,10,11,15,16,17,19,20,21],full:8,futur:[1,20],future_a:[1,17,18],future_a_tim:[1,17,18],future_admin:[1,17],g:[1,8,10,15,20],gener:[1,13,15],get:[1,5,8,15,21],get_add_liquidity_bonus_pct:[1,18],get_add_liquidity_fe:[1,18],get_amplifi:[1,18],get_app_ids_from_asset:[1,15],get_asset_price_after_liq_chang:[1,16],get_constant_product_minted_liquidity_token:[1,12],get_constant_product_zap_param:[1,21],get_escrow_address:[1,15],get_fe:[1,16],get_fee_from_gross_amount:[1,16],get_fee_from_net_amount:[1,16],get_hold:[1,10],get_invari:[1,18],get_liquid:[1,16],get_minimum_amount_receiv:[1,16],get_minted_liquidity_token:[1,12,16,18],get_new_liq:[1,18],get_other_asset:[1,15],get_pool_type_from_internal_st:[1,17],get_pric:[1,12,16,18],get_price_impact_pct:[1,16],get_secondary_added_liquidity_from_zap:[1,21],get_stableswap_minted_liquidity_token:[1,18],get_swap_amount_deposit:[1,12,16,18],get_swap_amount_deposited_from_zap:[1,21],get_swap_gross_amount_receiv:[1,12,16,18],get_swap_pric:[1,16],get_tx_fe:[1,18],get_zap_param:[1,21],getswapamountdeposit:[1,18],getswapgrossamountreceiv:[1,18],git:8,github:8,given:[1,10,11,15,16],global:[1,15,17],go:[1,16,19,21],gross:[1,16],gross_amount:[1,16],gross_amount_receiv:[1,12,18],group:[1,2,3,6,7,8,15,19,20,21],group_id:[1,2,3,6,7,20],ha:[1,8,10,16,18],have:[1,15,18,19,21],here:8,higher:[1,15],highli:[1,18],hold:[1,8,10],http:[1,8,11],human:[1,17],i:[1,15],id:[1,8,9,10,11,15,20],ignor:[1,16],impact:[1,16],implement:[1,12,18],inaccur:[1,18],includ:[1,16],increas:[1,18],index:[1,8,10,11,15],individu:[1,9],inform:[1,9,10,17],initi:[1,15],initial_a:[1,17,18],initial_a_tim:[1,17,18],initial_tot:[1,18],inner:[1,18],inspect:8,instanc:[1,10,11,15],instanti:[1,10,15,19,21],instead:[1,8,10,15,19,21],integ:[1,8,10,17],interact:[1,8,9,11],interfac:8,intern:[1,10,15,16,20],internal_st:[1,15],interpol:[1,18],inv:[1,18],invari:[1,18],invariant_iter:[1,18],io:8,irrelev:[1,15],is_asset_in_the_pool:[1,15],is_empti:[1,16],is_liquidity_token:[1,9],is_opted_in:[1,8,10],is_verifi:[1,9],iter:[1,18],its:4,keep:[1,18],kei:[1,9,17,20],kit:8,kv:[1,17],kwarg:[1,16],l:[1,17],larger:[1,15],last:[1,18],latest:8,left:[1,21],leftov:[1,21],length:[1,20],lessen:[1,16],let:8,librari:8,like:[1,16],limit:[1,8,9,18],linear:[1,18],liq_a:[1,12,16,18,21],liq_b:[1,12,16,18,21],liq_oth:[1,18],liquid:[1,3,5,7,8,9,10,11,15,16,18,21],liquidity_addit:[1,2,3,8,15,21],liquidity_asset:[1,2,3,7,8,15],liquidityaddit:[1,15,21],list:[1,9,11,15,17,20],list_pool:[1,8,9,11],listpoolsparam:[1,9,11],liter:[1,15,17],local:8,look:[1,10,15],loss:[1,10],low:[1,15,18],lower:[1,15],lp:[1,15],ltid:[1,17],mai:[1,10,11,15,18,21],make:[1,8,15,20],maker:8,manag:[1,8,10,19,20,21],manual:[1,8,10,15,19,21],map:[1,10],market:8,match:[1,9,11,15],math:[1,12,18],maximum:[1,15,19,21],meant:[1,21],meet:[1,9],method:[1,8,11,15,18],micro:[1,18],microalgo:8,minim:[1,10],minimum:[1,16],minimum_amount_receiv:[1,8,19],mint:[1,16,18],mint_tokens_invariant_iter:[1,18],miss:[1,10],mnemon:[2,3,6,7,8],modul:[0,8,9,11],more:[1,15,17],multipl:[1,8,15],must:[1,15],name:[1,9,10,15],necessari:8,need:[1,8,10,18,19,21],net:[1,16],net_amount:[1,16],net_amount_receiv:[1,16],net_amount_received_to_amount_deposit:[1,16],newton:[1,18],none:[1,10,11,17],normal:[1,19],note:[1,10,11,15,19],now:8,number:[1,10,18],numer:[1,16],object:[1,8,10,11,12,15,16,17,18,19,20,21],offset:[1,8,9],old:[1,15],omit:[1,9],one:[1,10,15,16,17,21],onli:[1,15,19,21],oper:[1,8,15,18],operationtyp:[1,15],opt:[1,2,3,6,7,8,10],opt_in:8,opt_in_tx:[3,8],opt_in_txn:[2,6,7],optin:[2,7],option:[1,8,9,10,11,15,17],order:[1,8,15],other:[1,15,16],other_asset:[1,10],other_coin:[1,8,11],otherwis:[1,10,15,16,19],out:[1,8,10,21],own:8,packag:[0,8],pact:[1,2,3,4,6,7,9,10,11,15,17],pact_api_url:[1,8,9,11,15],pact_fee_bp:[1,12,17,18,21],pactclient:[1,2,3,4,6,7,8,10,11,15],pactfi:8,pactsdk:[2,3,4,6,7,8,9,10,11,12,13,15,16,17,18,19,20,21],pactsdkerror:[1,13,15,18,20],page:8,pagin:[1,8,9,11],pair:8,param:[1,9,11,21],paramet:[1,8,9,10,11,15,16,17,18,19,20,21],pars:[1,15,17],parse_global_pool_st:[1,17],parse_internal_st:[1,15],parse_st:[1,17],particular:[1,19,21],pass:[1,9,10,11,15,20],paus:[1,15],per:[1,15,20],percent:[1,15,16],percentag:[1,19],perform:[1,3,6,7,15,19,21],period:8,pip:8,place:[1,10],plp:[1,21],plp_opt_in_txn:7,poetri:8,point:[1,10,11,15],pool:[0,2,3,5,6,7,8,9,10,11,12,14,16,17,18,19,21],pool_asset:[1,9],pool_calcul:[0,8,14],pool_stat:[0,8,14,15],pool_typ:[1,15],poolcalcul:[1,16],poolstat:[1,8,15,17],precis:[1,10,17,18],prepar:[1,15],prepare_:8,prepare_add_liq:[1,21],prepare_add_liquid:[1,2,3,8,15],prepare_add_liquidity_tx_group:[1,15],prepare_opt_in_tx:[1,2,3,6,7,8,10],prepare_remove_liquidity_tx_group:[1,8,15],prepare_swap:[1,6,8,15,19],prepare_swap_tx_group:[1,8,15],prepare_tx_group:[1,2,6,7,8,19,21],prepare_zap:[1,7,15,21],prepare_zap_tx_group:[1,15],price:[1,8,16,18,19],primari:[1,11,15,16],primary_add_liq:[1,21],primary_asset:[1,8,9,11,15],primary_asset__algoid:[1,8,9],primary_asset__nam:[1,9],primary_asset__unit_nam:[1,9],primary_asset_amount:[1,2,3,8,15,16],primary_asset_amount_decim:[1,16],primary_asset_index:[1,15],primary_asset_pric:[1,8,16,17],primary_asset_price_after_swap:[1,8,19],primary_asset_price_change_pct:[1,8,19],primary_fe:[1,17],primary_liq_chang:[1,16],print:[2,3,4,6,7,8],privat:[1,20],private_kei:[1,2,3,6,7,8,20],product:[1,8,12,15,21],proper:[1,15],properti:[1,10,15,16,18,20],protocol:[1,8,16],provid:[1,8,11,15,16],put:[1,20],py:8,pytest:8,python:[1,17],queri:[1,9,10,15],rais:[1,11,15,20],raphson:[1,18],ratio:[1,10],raw_stat:[1,17],re:[1,15],read:[1,4,15],readi:[1,10,19,21],receiv:[1,10,15,16,19],recommend:[1,15],regardless:8,relat:[1,16],relev:[1,11],remliq:[1,15],remov:[1,8,15],remove_liq_tx_group:8,repres:[1,15,19,21],represent:[1,10,17],requir:[1,8,15,18],respons:[1,9],result:[1,8,9],retri:[1,18],retriev:[1,8,11,17],round:[1,21],s:[1,8,15,16,17,19],same:[1,18],satisfi:[1,15],save_iter:[1,18],schema:[1,17],sdk:[1,10,11,18,20],search:8,second:[1,15,21],secondari:[1,11,15,16],secondary_add_liq:[1,21],secondary_asset:[1,8,9,11,15],secondary_asset__algoid:[1,9],secondary_asset__nam:[1,9],secondary_asset__unit_nam:[1,9],secondary_asset_amount:[1,2,3,8,15,16],secondary_asset_amount_decim:[1,16],secondary_asset_index:[1,15],secondary_asset_pric:[1,8,16,17],secondary_asset_price_after_swap:[1,8,19],secondary_asset_price_change_pct:[1,8,19],secondary_fe:[1,17],secondary_liq_chang:[1,16],see:[1,10,15],send:[1,8,10],send_transact:[2,3,6,7,8],sent_optin_txid:[2,6,7],sent_plp_optin_txid:7,set:[1,8,15,16,19,21],should:[1,10,21],si:[1,17],side:[1,19],sign:[1,2,3,6,7,8,19,20,21],sign_txn:8,signed_add_liq_tx_group:8,signed_group:[3,6,7],signed_remove_liq_tx_group:8,signed_tx:8,signed_tx_group:[2,8],signedtransact:[1,20],simul:[1,16,18],singl:[1,3,16,18,21],slippag:[1,15,16,18,19,21],slippage_pct:[1,6,7,8,15,16,19,21],smart:[1,18],so:[1,8,10],softwar:8,some:[1,15,21],sort:[1,16],specifi:[1,8,18],speed:[1,10],sqrt:[1,15],stableswap:[1,15,17,18,19,21],stableswap_calcul:[0,8,14],stableswap_param:[1,18],stableswapcalcul:[1,18],stableswapparam:[1,18],stale:[1,15],standard:[1,10,11],state:[1,5,8,15,17],statist:[1,16],store:[1,17,20],str:[1,9,10,11,15,17,19,20,21],string:[1,20],structur:[1,17],submit:8,submodul:0,suggest:[1,8,10,15],suggested_param:[1,3,10,15],suggestedparam:[1,10,15],support:[1,10,19],suppos:[1,15,16],swap:[0,5,8,10,14,15,16,18,21],swap_deposit:[1,21],swap_for_exact:[1,15,19],swap_invariant_iter:[1,18],swap_tx_group:[6,8],swapcalcul:[1,16],swapeffect:[1,8,19],t:[1,8,10,15,19,21],testb:8,testnet:8,than:[1,15],them:[1,16,19,21],thi:[1,2,3,4,6,7,8,9,10,11,15,16,17,18,19,20,21],those:[1,8,15,21],three:[1,15],through:[1,10],throughout:[1,13],thrown:[1,13],time:[1,10,19],timestamp:[1,18],to_private_kei:[2,3,6,7,8],token:[1,2,3,4,6,7,8,10,11,15,16,18,21],too:[1,15],top:8,total:[1,16,18],total_amount:[1,9,21],total_liquid:[1,8,12,17,18],total_primari:[1,8,12,17,18,21],total_secondari:[1,8,12,17,18,21],trade:[1,8,15,19,21],transact:[1,2,5,6,7,10,15,18,19,20,21],transaction_group:[0,8,14,15],transactiongroup:[1,3,8,15,19,20,21],treasuri:[1,17],tupl:[1,10,16,18],tvl_usd:[1,9],two:[1,8,11,15],tx:[1,3,15,18],tx_fee:[1,19],type:[1,9,10,11,12,15,16,17,18,19,20,21],typeddict:[1,9],typic:[1,10,11,15,19,21],unbalanc:[1,18],union:[1,11,15],unit:[1,10],unit_nam:[1,9,10],unsign:[1,17],up:[1,8,10],updat:[1,8,15],update_st:[1,8,15],updated_tot:[1,18],url:[1,2,3,4,6,7,8,9,11,15],us:[1,8,10,11,13,15,16,18,19,20,21],usag:[1,11],usdc:[2,3,4,6,7],user:[1,15,16,17,19,21],util:[1,10,17,19,21],v1:8,v2client:[1,2,3,4,6,7,8,10,11,15],valid:[1,8,11],valu:[1,8,10,16,17,18],versa:[1,15],version:[1,8,15,17],vice:[1,15],volume_24h:[1,9],volume_7d:[1,9],wa:[1,15,20],wai:[1,8,16],want:[1,8,10,16,19],we:[1,18],what:[1,8,19],when:[1,10,15,16,19,21],which:[1,8,11,15,16,21],whl:8,withdrawn:[1,15],within:[1,13,15],without:[1,10],work:[1,11,15,19,21],yet:[1,16],you:[1,8,10,15,19],your:8,zap:[0,5,8,14,15],zap_amount:[1,21],zap_tx_group:7,zapparam:[1,21],zero:[1,11,15,16,18,19]},titles:["pactsdk","pactsdk package","Add liquidity","Composing transactions","Get pool state","Examples","Swap","Zap","Pact Python SDK","api","asset","client","constant_product_calculator","exceptions","pactsdk","pool","pool_calculator","pool_state","stableswap_calculator","swap","transaction_group","zap"],titleterms:{add:2,api:[1,9],asset:[1,10],basic:8,build:8,client:[1,11],compos:[3,8],constant_product_calcul:[1,12],content:[1,8],develop:8,exampl:5,except:[1,13],get:4,indic:8,instal:8,liquid:2,list:8,modul:1,packag:1,pact:8,pactsdk:[0,1,14],pool:[1,4,15],pool_calcul:[1,16],pool_stat:[1,17],python:8,run:8,sdk:8,stableswap_calcul:[1,18],state:4,submodul:1,swap:[1,6,19],tabl:8,test:8,transact:[3,8],transaction_group:[1,20],usag:8,zap:[1,7,21]}})