Search.setIndex({docnames:["docs/source/modules","docs/source/pactsdk","examples/add_liquidity","examples/build_pool","examples/composing_transactions","examples/folks_lending_pool","examples/get_pool_state","examples/index","examples/list_pools","examples/swap","examples/zap","index","pactsdk/api","pactsdk/asset","pactsdk/client","pactsdk/config","pactsdk/constant_product_calculator","pactsdk/exceptions","pactsdk/factories","pactsdk/folks_lending_pool","pactsdk/index","pactsdk/pool","pactsdk/pool_calculator","pactsdk/pool_state","pactsdk/stableswap_calculator","pactsdk/swap","pactsdk/transaction_group","pactsdk/zap"],envversion:{"sphinx.domains.c":2,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":5,"sphinx.domains.index":1,"sphinx.domains.javascript":2,"sphinx.domains.math":2,"sphinx.domains.python":3,"sphinx.domains.rst":2,"sphinx.domains.std":2,sphinx:56},filenames:["docs/source/modules.rst","docs/source/pactsdk.rst","examples/add_liquidity.rst","examples/build_pool.rst","examples/composing_transactions.rst","examples/folks_lending_pool.rst","examples/get_pool_state.rst","examples/index.rst","examples/list_pools.rst","examples/swap.rst","examples/zap.rst","index.rst","pactsdk/api.rst","pactsdk/asset.rst","pactsdk/client.rst","pactsdk/config.rst","pactsdk/constant_product_calculator.rst","pactsdk/exceptions.rst","pactsdk/factories.rst","pactsdk/folks_lending_pool.rst","pactsdk/index.rst","pactsdk/pool.rst","pactsdk/pool_calculator.rst","pactsdk/pool_state.rst","pactsdk/stableswap_calculator.rst","pactsdk/swap.rst","pactsdk/transaction_group.rst","pactsdk/zap.rst"],objects:{"":[[1,0,0,"-","pactsdk"]],"pactsdk.api":[[12,1,1,"","ApiAsset"],[12,1,1,"","ApiListPoolsResponse"],[12,1,1,"","ApiPool"],[12,1,1,"","ListPoolsParams"],[12,3,1,"","list_pools"]],"pactsdk.api.ApiAsset":[[12,2,1,"","algoid"],[12,2,1,"","decimals"],[12,2,1,"","id"],[12,2,1,"","is_liquidity_token"],[12,2,1,"","is_verified"],[12,2,1,"","name"],[12,2,1,"","total_amount"],[12,2,1,"","tvl_usd"],[12,2,1,"","unit_name"],[12,2,1,"","volume_24h"],[12,2,1,"","volume_7d"]],"pactsdk.api.ApiListPoolsResponse":[[12,2,1,"","count"],[12,2,1,"","limit"],[12,2,1,"","offset"],[12,2,1,"","results"]],"pactsdk.api.ApiPool":[[12,2,1,"","address"],[12,2,1,"","appid"],[12,2,1,"","apr_7d"],[12,2,1,"","confirmed_round"],[12,2,1,"","creator"],[12,2,1,"","fee_amount_24h"],[12,2,1,"","fee_amount_7d"],[12,2,1,"","fee_usd_24h"],[12,2,1,"","fee_usd_7d"],[12,2,1,"","id"],[12,2,1,"","is_verified"],[12,2,1,"","pool_asset"],[12,2,1,"","primary_asset"],[12,2,1,"","secondary_asset"],[12,2,1,"","tvl_usd"],[12,2,1,"","volume_24h"],[12,2,1,"","volume_7d"]],"pactsdk.api.ListPoolsParams":[[12,2,1,"","creator"],[12,2,1,"","is_verified"],[12,2,1,"","limit"],[12,2,1,"","offset"],[12,2,1,"","primary_asset__algoid"],[12,2,1,"","primary_asset__name"],[12,2,1,"","primary_asset__unit_name"],[12,2,1,"","secondary_asset__algoid"],[12,2,1,"","secondary_asset__name"],[12,2,1,"","secondary_asset__unit_name"]],"pactsdk.asset":[[13,4,1,"","ASSETS_CACHE"],[13,1,1,"","Asset"],[13,3,1,"","fetch_asset_by_index"],[13,3,1,"","get_cached_asset"]],"pactsdk.asset.Asset":[[13,5,1,"","__eq__"],[13,2,1,"","algod"],[13,5,1,"","build_opt_in_tx"],[13,5,1,"","build_opt_out_tx"],[13,5,1,"","build_transfer_tx"],[13,2,1,"","decimals"],[13,5,1,"","get_holding"],[13,5,1,"","get_holding_from_account_info"],[13,2,1,"","index"],[13,5,1,"","is_opted_in"],[13,2,1,"","name"],[13,5,1,"","prepare_opt_in_tx"],[13,5,1,"","prepare_opt_out_tx"],[13,6,1,"","ratio"],[13,2,1,"","unit_name"]],"pactsdk.client":[[14,1,1,"","PactClient"]],"pactsdk.client.PactClient":[[14,5,1,"","__init__"],[14,2,1,"","algod"],[14,2,1,"","config"],[14,2,1,"","farming"],[14,5,1,"","fetch_asset"],[14,5,1,"","fetch_folks_lending_pool"],[14,5,1,"","fetch_pool_by_id"],[14,5,1,"","fetch_pools_by_assets"],[14,5,1,"","get_constant_product_pool_factory"],[14,5,1,"","get_folks_lending_pool_adapter"],[14,5,1,"","get_nft_constant_product_pool_factory"],[14,5,1,"","list_pools"]],"pactsdk.config":[[15,1,1,"","Config"],[15,3,1,"","get_config"]],"pactsdk.config.Config":[[15,2,1,"","api_url"],[15,2,1,"","factory_constant_product_id"],[15,2,1,"","factory_nft_constant_product_id"],[15,2,1,"","folks_lending_pool_adapter_id"],[15,2,1,"","gas_station_id"]],"pactsdk.constant_product_calculator":[[16,1,1,"","ConstantProductCalculator"],[16,1,1,"","ConstantProductParams"],[16,3,1,"","get_constant_product_minted_liquidity_tokens"],[16,3,1,"","get_swap_amount_deposited"],[16,3,1,"","get_swap_gross_amount_received"]],"pactsdk.constant_product_calculator.ConstantProductCalculator":[[16,5,1,"","get_minted_liquidity_tokens"],[16,5,1,"","get_price"],[16,5,1,"","get_swap_amount_deposited"],[16,5,1,"","get_swap_gross_amount_received"]],"pactsdk.constant_product_calculator.ConstantProductParams":[[16,2,1,"","fee_bps"],[16,2,1,"","pact_fee_bps"]],"pactsdk.exceptions":[[17,7,1,"","PactSdkError"]],"pactsdk.factories":[[18,0,0,"-","base_factory"],[18,0,0,"-","constant_product"],[18,0,0,"-","get_pool_factory"]],"pactsdk.factories.base_factory":[[18,1,1,"","FactoryState"],[18,1,1,"","PoolBuildParams"],[18,1,1,"","PoolFactory"],[18,1,1,"","PoolParams"],[18,3,1,"","fetch_pool_id"],[18,3,1,"","get_contract_deploy_cost"],[18,3,1,"","list_pools"],[18,3,1,"","parse_global_factory_state"]],"pactsdk.factories.base_factory.FactoryState":[[18,2,1,"","allowed_fee_bps"],[18,2,1,"","pool_version"]],"pactsdk.factories.base_factory.PoolBuildParams":[[18,2,1,"","fee_bps"],[18,2,1,"","primary_asset_id"],[18,2,1,"","secondary_asset_id"]],"pactsdk.factories.base_factory.PoolFactory":[[18,2,1,"","algod"],[18,2,1,"","app_id"],[18,5,1,"","build"],[18,5,1,"","build_or_get"],[18,5,1,"","build_tx_group"],[18,5,1,"","fetch_pool"],[18,5,1,"","fetch_pool_id"],[18,5,1,"","list_pools"],[18,2,1,"","state"]],"pactsdk.factories.base_factory.PoolParams":[[18,2,1,"","abi"],[18,5,1,"","as_tuple"],[18,2,1,"","fee_bps"],[18,5,1,"","from_box_name"],[18,2,1,"","primary_asset_id"],[18,2,1,"","secondary_asset_id"],[18,5,1,"","to_box_name"],[18,2,1,"","version"]],"pactsdk.factories.constant_product":[[18,1,1,"","ConstantProductFactory"],[18,3,1,"","build_constant_product_tx_group"]],"pactsdk.factories.constant_product.ConstantProductFactory":[[18,5,1,"","build_tx_group"]],"pactsdk.factories.get_pool_factory":[[18,3,1,"","get_pool_factory"]],"pactsdk.folks_lending_pool":[[19,1,1,"","FolksLendingPool"],[19,1,1,"","FolksLendingPoolAdapter"],[19,1,1,"","LendingLiquidityAddition"],[19,1,1,"","LendingSwap"],[19,3,1,"","fetch_folks_lending_pool"]],"pactsdk.folks_lending_pool.FolksLendingPool":[[19,2,1,"","algod"],[19,2,1,"","app_id"],[19,5,1,"","convert_deposit"],[19,5,1,"","convert_withdraw"],[19,2,1,"","deposit_interest_index"],[19,2,1,"","deposit_interest_rate"],[19,2,1,"","escrow_address"],[19,2,1,"","f_asset"],[19,5,1,"","get_last_timestamp"],[19,2,1,"","last_timestamp_override"],[19,2,1,"","manager_app_id"],[19,2,1,"","original_asset"],[19,2,1,"","updated_at"]],"pactsdk.folks_lending_pool.FolksLendingPoolAdapter":[[19,2,1,"","algod"],[19,2,1,"","app_id"],[19,5,1,"","build_add_liquidity_txs"],[19,5,1,"","build_opt_in_to_asset_tx_group"],[19,5,1,"","build_remove_liquidity_txs"],[19,5,1,"","build_swap_txs"],[19,2,1,"","escrow_address"],[19,5,1,"","f_asset_to_original_asset"],[19,5,1,"","original_asset_to_f_asset"],[19,2,1,"","pact_pool"],[19,5,1,"","prepare_add_liquidity"],[19,5,1,"","prepare_add_liquidity_tx_group"],[19,5,1,"","prepare_opt_in_to_asset_tx_group"],[19,5,1,"","prepare_remove_liquidity_tx_group"],[19,5,1,"","prepare_swap"],[19,5,1,"","prepare_swap_tx_group"],[19,2,1,"","primary_lending_pool"],[19,2,1,"","secondary_lending_pool"]],"pactsdk.folks_lending_pool.LendingLiquidityAddition":[[19,2,1,"","lending_pool_adapter"],[19,2,1,"","liquidity_addition"],[19,2,1,"","primary_asset_amount"],[19,2,1,"","secondary_asset_amount"]],"pactsdk.folks_lending_pool.LendingSwap":[[19,2,1,"","amount_deposited"],[19,2,1,"","amount_received"],[19,2,1,"","asset_deposited"],[19,2,1,"","asset_received"],[19,2,1,"","f_swap"],[19,2,1,"","minimum_amount_received"],[19,2,1,"","tx_fee"]],"pactsdk.pool":[[21,4,1,"","OperationType"],[21,1,1,"","Pool"],[21,3,1,"","fetch_app_global_state"],[21,3,1,"","fetch_pool_by_id"],[21,3,1,"","fetch_pools_by_assets"],[21,3,1,"","get_app_ids_from_assets"]],"pactsdk.pool.Pool":[[21,5,1,"","__eq__"],[21,2,1,"","algod"],[21,2,1,"","app_id"],[21,5,1,"","build_add_liquidity_txs"],[21,5,1,"","build_raw_add_liquidity_txs"],[21,5,1,"","build_remove_liquidity_txs"],[21,5,1,"","build_swap_txs"],[21,5,1,"","build_zap_txs"],[21,2,1,"","fee_bps"],[21,5,1,"","get_escrow_address"],[21,5,1,"","get_other_asset"],[21,2,1,"","internal_state"],[21,5,1,"","is_asset_in_the_pool"],[21,2,1,"","liquidity_asset"],[21,5,1,"","parse_internal_state"],[21,2,1,"","pool_type"],[21,5,1,"","prepare_add_liquidity"],[21,5,1,"","prepare_add_liquidity_tx_group"],[21,5,1,"","prepare_remove_liquidity_tx_group"],[21,5,1,"","prepare_swap"],[21,5,1,"","prepare_swap_tx_group"],[21,5,1,"","prepare_zap"],[21,5,1,"","prepare_zap_tx_group"],[21,2,1,"","primary_asset"],[21,2,1,"","secondary_asset"],[21,5,1,"","update_state"],[21,2,1,"","version"]],"pactsdk.pool_calculator":[[22,1,1,"","PoolCalculator"],[22,1,1,"","SwapCalculator"]],"pactsdk.pool_calculator.PoolCalculator":[[22,5,1,"","amount_deposited_to_net_amount_received"],[22,5,1,"","get_asset_price_after_liq_change"],[22,5,1,"","get_fee"],[22,5,1,"","get_fee_from_gross_amount"],[22,5,1,"","get_fee_from_net_amount"],[22,5,1,"","get_liquidities"],[22,5,1,"","get_minimum_amount_received"],[22,5,1,"","get_price_impact_pct"],[22,5,1,"","get_swap_price"],[22,6,1,"","is_empty"],[22,5,1,"","net_amount_received_to_amount_deposited"],[22,6,1,"","primary_asset_amount"],[22,6,1,"","primary_asset_amount_decimal"],[22,6,1,"","primary_asset_price"],[22,6,1,"","secondary_asset_amount"],[22,6,1,"","secondary_asset_amount_decimal"],[22,6,1,"","secondary_asset_price"]],"pactsdk.pool_calculator.SwapCalculator":[[22,5,1,"","get_minted_liquidity_tokens"],[22,5,1,"","get_price"],[22,5,1,"","get_swap_amount_deposited"],[22,5,1,"","get_swap_gross_amount_received"],[22,2,1,"","pool"]],"pactsdk.pool_state":[[23,1,1,"","AppInternalState"],[23,1,1,"","PoolState"],[23,3,1,"","get_pool_type_from_internal_state"],[23,3,1,"","parse_global_pool_state"]],"pactsdk.pool_state.AppInternalState":[[23,2,1,"","A"],[23,2,1,"","ADMIN"],[23,2,1,"","ASSET_A"],[23,2,1,"","ASSET_B"],[23,2,1,"","B"],[23,2,1,"","CONTRACT_NAME"],[23,2,1,"","FEE_BPS"],[23,2,1,"","FUTURE_A"],[23,2,1,"","FUTURE_ADMIN"],[23,2,1,"","FUTURE_A_TIME"],[23,2,1,"","INITIAL_A"],[23,2,1,"","INITIAL_A_TIME"],[23,2,1,"","L"],[23,2,1,"","LTID"],[23,2,1,"","PACT_FEE_BPS"],[23,2,1,"","PRECISION"],[23,2,1,"","PRIMARY_FEES"],[23,2,1,"","SECONDARY_FEES"],[23,2,1,"","TREASURY"],[23,2,1,"","VERSION"]],"pactsdk.pool_state.PoolState":[[23,2,1,"","primary_asset_price"],[23,2,1,"","secondary_asset_price"],[23,2,1,"","total_liquidity"],[23,2,1,"","total_primary"],[23,2,1,"","total_secondary"]],"pactsdk.stableswap_calculator":[[24,7,1,"","ConvergenceError"],[24,1,1,"","StableswapCalculator"],[24,1,1,"","StableswapParams"],[24,3,1,"","get_add_liquidity_bonus_pct"],[24,3,1,"","get_add_liquidity_fees"],[24,3,1,"","get_amplifier"],[24,3,1,"","get_invariant"],[24,3,1,"","get_new_liq"],[24,3,1,"","get_stableswap_minted_liquidity_tokens"],[24,3,1,"","get_swap_amount_deposited"],[24,3,1,"","get_swap_gross_amount_received"],[24,3,1,"","get_tx_fee"]],"pactsdk.stableswap_calculator.StableswapCalculator":[[24,5,1,"","_get_price"],[24,5,1,"","get_amplifier"],[24,5,1,"","get_minted_liquidity_tokens"],[24,5,1,"","get_price"],[24,5,1,"","get_swap_amount_deposited"],[24,5,1,"","get_swap_gross_amount_received"],[24,2,1,"","mint_tokens_invariant_iterations"],[24,6,1,"","stableswap_params"],[24,2,1,"","swap_invariant_iterations"]],"pactsdk.stableswap_calculator.StableswapParams":[[24,2,1,"","fee_bps"],[24,2,1,"","future_a"],[24,2,1,"","future_a_time"],[24,2,1,"","initial_a"],[24,2,1,"","initial_a_time"],[24,2,1,"","pact_fee_bps"],[24,2,1,"","precision"]],"pactsdk.swap":[[25,1,1,"","Swap"],[25,1,1,"","SwapEffect"]],"pactsdk.swap.Swap":[[25,2,1,"","amount"],[25,2,1,"","asset_deposited"],[25,2,1,"","asset_received"],[25,2,1,"","effect"],[25,2,1,"","pool"],[25,5,1,"","prepare_tx_group"],[25,2,1,"","slippage_pct"],[25,2,1,"","swap_for_exact"]],"pactsdk.swap.SwapEffect":[[25,2,1,"","amount_deposited"],[25,2,1,"","amount_received"],[25,2,1,"","amplifier"],[25,2,1,"","fee"],[25,2,1,"","minimum_amount_received"],[25,2,1,"","price"],[25,2,1,"","primary_asset_price_after_swap"],[25,2,1,"","primary_asset_price_change_pct"],[25,2,1,"","secondary_asset_price_after_swap"],[25,2,1,"","secondary_asset_price_change_pct"],[25,2,1,"","tx_fee"]],"pactsdk.transaction_group":[[26,1,1,"","TransactionGroup"]],"pactsdk.transaction_group.TransactionGroup":[[26,5,1,"","__init__"],[26,6,1,"","group_id"],[26,5,1,"","sign"],[26,2,1,"","transactions"]],"pactsdk.zap":[[27,1,1,"","Zap"],[27,1,1,"","ZapParams"],[27,3,1,"","get_constant_product_zap_params"],[27,3,1,"","get_secondary_added_liquidity_from_zapping"],[27,3,1,"","get_swap_amount_deposited_from_zapping"]],"pactsdk.zap.Zap":[[27,2,1,"","amount"],[27,2,1,"","asset"],[27,5,1,"","get_zap_params"],[27,2,1,"","liquidity_addition"],[27,2,1,"","params"],[27,2,1,"","pool"],[27,5,1,"","prepare_add_liq"],[27,5,1,"","prepare_tx_group"],[27,2,1,"","slippage_pct"],[27,2,1,"","swap"]],"pactsdk.zap.ZapParams":[[27,2,1,"","primary_add_liq"],[27,2,1,"","secondary_add_liq"],[27,2,1,"","swap_deposited"]],pactsdk:[[12,0,0,"-","api"],[13,0,0,"-","asset"],[14,0,0,"-","client"],[15,0,0,"-","config"],[16,0,0,"-","constant_product_calculator"],[17,0,0,"-","exceptions"],[19,0,0,"-","folks_lending_pool"],[21,0,0,"-","pool"],[22,0,0,"-","pool_calculator"],[23,0,0,"-","pool_state"],[24,0,0,"-","stableswap_calculator"],[25,0,0,"-","swap"],[26,0,0,"-","transaction_group"],[27,0,0,"-","zap"]]},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","attribute","Python attribute"],"3":["py","function","Python function"],"4":["py","data","Python data"],"5":["py","method","Python method"],"6":["py","property","Python property"],"7":["py","exception","Python exception"]},objtypes:{"0":"py:module","1":"py:class","2":"py:attribute","3":"py:function","4":"py:data","5":"py:method","6":"py:property","7":"py:exception"},terms:{"0":[1,2,3,5,6,8,9,10,11,14,15,18,21,24,26],"091142966447585":11,"1":[5,11],"10":[1,21,24],"100":[3,5],"1000":[1,21],"100_000":[4,5,9,10,11],"12345678":[1,14],"1255182523659604":11,"14111329":3,"143598":11,"146529":11,"147169673":5,"147170678":5,"1_000_000":[2,11],"2":[1,5,9,10,11,21],"200000":11,"200_000":[4,11],"20_000":5,"3":[1,21],"30":[1,21],"31":11,"31566704":[2,6,9,10],"441":11,"456321":11,"46":11,"500_000":2,"50_000":11,"549580645715963":11,"6":[1,24],"6081680080300244":11,"620995314":4,"64":[1,21],"6442824791774173":11,"73485":11,"849972":11,"8884795940873393":11,"8949213":11,"900000":11,"956659":11,"abstract":18,"byte":18,"case":[1,24],"class":[1,12,13,14,15,16,18,19,21,22,23,24,25,26,27],"default":[1,11,19,21],"do":[1,9,10,25],"float":[1,13,16,21,22,23,24,25,27],"function":[1,12,13,21,22,24],"import":[1,2,3,4,5,6,8,9,10,11,14],"int":[1,12,13,14,15,16,18,19,21,22,23,24,25,27],"new":[1,3,18,21,22],"return":[1,11,12,13,14,15,16,18,19,21,22,23,24,25,26,27],"true":[1,13,18,21,22,24,25],"try":[1,24],A:[1,13,14,18,19,21,22,23,24,25,26,27],By:11,For:[1,19,21,27],If:[1,14,21,25,26],In:[1,13,14,21,24],It:[1,8,11,14,18,19,25],One:[1,21],The:[1,11,12,13,14,17,18,19,21,22,23,24,25,26,27],There:[1,11,21],To:[1,8,19,24],__eq__:[1,13,21],__init__:[1,14,26],__version__:11,_get_pric:[1,24],_tx:11,_tx_group:11,abi:18,abl:[1,13],about:[1,12,13,14,19,22],abov:[1,19,21],accept:[1,21,22],accommod:[1,19],accord:[1,14],account:[1,2,3,4,5,8,9,10,11,13,21,25,27],account_info:[1,13],across:[1,14],action:5,actual:[1,13,18,19],ad:[1,5,19,21,22,24,27],adapt:[1,5,14,19],add:[1,4,5,7,11,19,21,22,27],add_liq_tx_group:[2,11],add_liquid:[1,19,27],add_liquidity_tx:4,added_liq_a:[1,16,22,24],added_liq_b:[1,16,22,24],added_primari:[1,16,24],added_secondari:[1,16,24],addit:[1,21,24,27],addliq:[1,21],address:[1,2,3,4,5,8,9,10,11,12,13,18,19,21,25,27],address_from_private_kei:[2,3,4,5,8,9,10,11],admin:[1,23],after:[1,11,19,22],algo:[1,2,4,5,6,9,10,11,14,19,21],algod:[1,2,3,4,5,6,8,9,10,11,13,14,18,19,21],algodcli:[1,2,3,4,5,6,8,9,10,11,13,14,18,19,21],algodhttperror:[1,14],algoid:[1,12],algorand:[1,11,13,14,21,24,26],algosdk:[1,2,3,4,5,6,8,9,10,11,13,14,18,19,21,23,26],alia:[1,21],all:[1,5,12,14,18,21,24,26,27],allow:[1,13,14,18,19,21,25,27],allowed_fee_bp:18,alreadi:[1,3,13,22],also:[1,11,13],amm:[1,21,23],amount:[1,5,9,10,11,13,19,21,22,24,25,27],amount_deposit:[1,11,16,19,22,24,25],amount_deposited_to_net_amount_receiv:[1,22],amount_receiv:[1,11,19,22,25],amountdeposit:[1,22],amountreceiv:[1,22],amp:[1,24],amplifi:[1,24,25],an:[1,5,13,14,16,18,21,24,25,26],ani:[1,21],api:[0,11,14,20,21],api_url:[1,15],apiasset:[1,12],apilistpoolsrespons:[1,12,14],apipool:[1,12],app:[1,11,14,21,24],app_id:[1,14,18,19,21],appid:[1,12],appinternalst:[1,21,23],applic:[1,14,18,19,21],apr:[1,14,19],apr_7d:[1,12],ar:[1,11,12,13,14,18,19,21,22,25,27],architectur:8,arg:[1,22],argument:11,around:[1,19],arrai:[1,22,26],array_static_typ:18,arraystatictyp:18,as_tupl:18,asa:[1,13,14],ask:11,assertionerror:[1,21],asset:[0,4,5,9,10,11,12,14,19,20,21,22,25,27],asset_a:[1,21,23],asset_b:[1,21,23],asset_deposit:[1,19,22,25],asset_id:[1,5,19],asset_index:[1,14],asset_receiv:[1,19,25],assets_cach:[1,13],assettransfertxn:[1,13],assign:[1,26],atom:4,autom:11,automat:[1,13],avail:[1,24],b:[1,21,23],backward:[1,14],base64:[1,26],base:[1,12,13,14,15,16,17,18,19,21,22,23,24,25,26,27],base_factori:18,basi:[1,21],basic:[1,5,12,13,21,25],befor:[1,8,11,13,19],behavior:[1,19],behind:[1,16,24],between:[1,13,14,19,21],block:[1,19],blockchain:[1,14,21],bool:[1,12,13,18,21,22,25],both:[1,19,21,24,27],box:[1,18,27],build:[1,7,18,19,21],build_:11,build_add_liquidity_tx:[1,4,19,21],build_constant_product_tx_group:18,build_opt_in_to_asset_tx_group:[1,19],build_opt_in_tx:[1,13],build_opt_out_tx:[1,13],build_or_get:[3,5,18],build_raw_add_liquidity_tx:[1,21],build_remove_liquidity_tx:[1,19,21],build_swap_tx:[1,11,19,21],build_transfer_tx:[1,13],build_tx_group:18,build_zap_tx:[1,21],buildaddliquiditytx:[1,21],buildswaptx:[1,21],built:[1,21],burn:[1,21],c:11,cach:[1,13],calcul:[1,19,22,24,25],call:[1,12,13,14,18,19,21,24],callabl:18,callback:18,can:[1,11,12,14,18,21],caution:11,cd:11,ceil:[1,19],certain:[1,22],chain:[1,11,14],chang:[1,11,14,22],check:[1,11,13,21,22],choic:8,chosen:[1,14],circumst:[1,21],classmethod:18,client:[0,11,13,20,21,25],clone:11,close_to:[1,13],com:11,combin:[1,19],commit:[1,25,27],compar:[1,13,21],compat:[1,14],compos:[1,7,14,19],comput:[1,25],config:[0,11,14,18,20],configur:[1,11,14],confirmed_round:[1,12],constant:[1,8,14,16,21,27],constant_product:[1,18,21,23],constant_product_calcul:[0,11,20],constantproductcalcul:[1,16],constantproductfactori:[1,14,18],constantproductparam:[1,16],construct:[1,21,25],constructor:[1,14],contain:[1,11,12,22],content:[0,18],contract:[1,11,14,18,19,21,22,23,24,25],contract_nam:[1,23],conveni:[1,11,14,26],convergenceerror:[1,24],convers:[1,19],convert:[1,13,19,22],convert_deposit:[1,19],convert_withdraw:[1,19],correspond:[1,19,21],count:[1,12],cover:11,creat:[1,3,5,8,11,13,14,18,19,21,24,25,26,27],creation:[1,18,21],creator:[1,12],current:[1,11,13,19,22],d:11,data:[1,12,13,14,21,22],datetim:[1,19],deal:[1,13],decentr:[11,18],decim:[1,12,13,22],dedic:8,def:11,depend:[1,14,19,25],deploi:[3,18],deposit:[1,19,21,22,25],deposit_interest_index:[1,19],deposit_interest_r:[1,19],deprec:[1,14],describ:[1,13],detail:[1,12,13,14,21,25],dev:[1,14],develop:[1,14],dict:[1,12,13],dictionari:[1,13],differ:[1,11,21,22,24],directli:[1,11,14,19],discover:[1,14,18],dist:11,doc:[1,14],docker:11,document:11,doe:[1,14,18],doesn:[1,3,19],don:[1,13,21,25,27],due:[1,26,27],dure:[1,27],e:[1,11,13,18,19,21,26],each:[1,8,11,18,24,26],easier:[1,26],easili:11,effect:[1,11,25],either:[1,22,25],els:3,empti:[1,14,21,22,24,26],enabl:[1,21],encod:[1,26],enhanc:11,ensur:[1,18,21],entri:[1,14],equal:[1,13,21],error:[1,14],escrow:[1,21],escrow_address:[1,19],etc:[1,14],everi:[1,13,18],exact:[1,22,25],exampl:[1,2,3,4,5,6,8,9,10,11,14],except:[0,11,20,24],exchang:[1,22,25,27],execut:[1,21,25,27],exist:[1,3,14,18],experi:11,explicit:11,explicitli:[1,13],expos:[1,14,21],express:[1,21],extend:11,extra:[1,24],extra_margin:[1,24],extra_pag:18,extract:[1,13],f:[2,4,6,9,10],f_asset:[1,5,19],f_asset_to_original_asset:[1,19],f_swap:[1,19],factori:[0,3,5,8,11,14,20],factory_constant_product_id:[1,15],factory_id:18,factory_nft_constant_product_id:[1,15],factoryst:18,fail:[1,21,24],failur:[1,26],falgo:[1,19],fals:[1,13,18,19,21,22,25],farm:[1,11,14],farming_cli:[1,14],fasset:[1,14,19],featur:[1,21],fee:[1,11,21,22,24,25],fee_amount_24h:[1,12],fee_amount_7d:[1,12],fee_bp:[1,3,5,11,16,18,21,22,23,24,27],fee_usd_24h:[1,12],fee_usd_7d:[1,12],fetch:[1,5,6,8,11,13,14,18,19,21],fetch_app_global_st:[1,21],fetch_asset:[1,2,6,9,10,11,13,14],fetch_asset_by_index:[1,13],fetch_folks_lending_pool:[1,5,14,19],fetch_pool:[8,18],fetch_pool_by_id:[1,4,11,13,14,21],fetch_pool_id:18,fetch_pools_by_asset:[1,2,6,9,10,11,14,21],field:[1,19],financ:[1,14,19],find:[1,12,14,21],first:[1,14,18],flag:[1,21],folk:[1,7,11,14,19],folks_lending_pool:[0,11,14,20],folks_lending_pool_adapter_id:[1,15],folks_lending_pool_id:5,folks_pool_a:5,folks_pool_b:5,folkslendingpool:[1,14,19],folkslendingpooladapt:[1,14,19],formula:[1,21,22],found:11,fresh:11,friendli:[1,23],from:[1,2,3,4,5,6,8,9,10,11,12,13,14,18,19,21,22,23,25,26,27],from_box_nam:18,full:11,fulli:8,fusdc:[1,19],futur:[1,14],future_a:[1,23,24],future_a_tim:[1,23,24],future_admin:[1,23],g:[1,11,13,18,19,21,26],gas_station_id:[1,15],gener:[1,17,21],get:[1,7,11,14,21,27],get_add_liquidity_bonus_pct:[1,24],get_add_liquidity_fe:[1,24],get_amplifi:[1,24],get_app_ids_from_asset:[1,21],get_asset_price_after_liq_chang:[1,22],get_cached_asset:[1,13],get_config:[1,15],get_constant_product_minted_liquidity_token:[1,16],get_constant_product_pool_factori:[1,3,5,8,14],get_constant_product_zap_param:[1,27],get_contract_deploy_cost:18,get_escrow_address:[1,21],get_fe:[1,22],get_fee_from_gross_amount:[1,22],get_fee_from_net_amount:[1,22],get_folks_lending_pool_adapt:[1,5,14],get_hold:[1,13],get_holding_from_account_info:[1,13],get_invari:[1,24],get_last_timestamp:[1,19],get_liquid:[1,22],get_minimum_amount_receiv:[1,22],get_minted_liquidity_token:[1,16,22,24],get_new_liq:[1,24],get_nft_constant_product_pool_factori:[1,14],get_other_asset:[1,21],get_pool_factori:18,get_pool_type_from_internal_st:[1,23],get_pric:[1,16,22,24],get_price_impact_pct:[1,22],get_secondary_added_liquidity_from_zap:[1,27],get_stableswap_minted_liquidity_token:[1,24],get_swap_amount_deposit:[1,16,22,24],get_swap_amount_deposited_from_zap:[1,27],get_swap_gross_amount_receiv:[1,16,22,24],get_swap_pric:[1,22],get_tx_fe:[1,24],get_zap_param:[1,27],getswapamountdeposit:[1,24],getswapgrossamountreceiv:[1,24],git:11,github:11,given:[1,3,13,14,18,21,22],global:[1,11,14,18,19,21,23],go:[1,18,22,25,27],gross:[1,22],gross_amount:[1,22],gross_amount_receiv:[1,16,24],group:[1,2,4,9,10,11,21,25,26,27],group_id:[1,2,4,5,9,10,26],ha:[1,11,13,18,22,24],hash:18,have:[1,18,19,21,24,25,27],here:[1,11,14],hidden:[1,19],higher:[1,14,19,21],highli:[1,24],hold:[1,11,13],http:[1,11,14],i:[1,21],id:[1,11,12,13,14,18,21,26],ignor:[1,22],impact:[1,22],implement:[1,16,24],inaccur:[1,24],includ:[1,22],increas:[1,24],index:[1,5,11,13,14,21],individu:[1,12],info:[1,19],inform:[1,12,13,19],initi:[1,21],initial_a:[1,23,24],initial_a_tim:[1,23,24],initial_tot:[1,24],inner:[1,19,24],inspect:11,instanc:[1,13,14,18,21],instanti:[1,13,21,25,27],instead:[1,11,13,19,21,25,27],integ:[1,11,13],interact:[1,11,12,14,19],interfac:[1,11,19],intern:[1,13,21,22,26],internal_st:[1,21],interpol:[1,24],introduc:8,inv:[1,24],invari:[1,24],invariant_iter:[1,24],io:11,irrelev:[1,21],is_algo:18,is_asset_in_the_pool:[1,21],is_empti:[1,22],is_liquidity_token:[1,12],is_opted_in:[1,11,13],is_verifi:[1,12],item:18,iter:[1,24],its:6,keep:[1,24],kei:[1,12,26],kept:[1,14],kit:11,kwarg:[1,14,15,22],l:[1,23],lambda:[3,5],larger:[1,21],last:[1,19,24],last_timestamp_overrid:[1,19],latest:11,leav:[1,19],left:[1,27],leftov:[1,27],lend:[1,7,11,14,19],lending_pool_adapt:[1,5,19],lendingliquidityaddit:[1,19],lendingswap:[1,19],length:[1,26],lessen:[1,22],let:11,librari:11,like:[1,11,22],limit:[1,12,24],linear:[1,24],liq_a:[1,16,22,24,27],liq_b:[1,16,22,24,27],liq_oth:[1,24],liquid:[1,4,5,7,10,11,12,13,14,19,21,22,24,27],liquidity_addit:[1,2,4,5,11,19,21,27],liquidity_asset:[1,2,4,5,10,11,21],liquidityaddit:[1,19,21,27],list:[1,7,12,14,18,19,21,23,26],list_pool:[1,8,12,14,18],listpoolsparam:[1,12,14],liter:[1,14,21,23],local:11,look:[1,13,18,21],loss:[1,13],low:[1,21,24],lower:[1,21],lp:[1,21],ltid:[1,23],mai:[1,13,14,21,24,27],mainnet:[1,11,14],make:[1,5,11,19,21,26],maker:11,manag:[1,11,13,25,26,27],manager_app_id:[1,19],manual:[1,11,13,21,25,27],map:[1,13,18],market:11,match:[1,12,14,21],math:[1,16,24],maximum:[1,21,25,27],mean:18,meant:[1,27],meet:[1,12],method:[1,11,14,18,19,21,24],micro:[1,24],microalgo:11,mimic:[1,19],minim:[1,13,19],minimum:[1,22],minimum_amount_receiv:[1,11,19,25],mint:[1,22,24],mint_tokens_invariant_iter:[1,24],miss:[1,13],mnemon:[2,3,4,5,8,9,10,11],modul:[0,11,12,14,19],more:[1,21],multipl:[1,11,21],must:[1,21],name:[1,12,13,18,21],necessari:11,need:[1,11,13,19,24,25,27],net:[1,22],net_amount:[1,22],net_amount_receiv:[1,22],net_amount_received_to_amount_deposit:[1,22],network:[1,2,3,4,5,6,8,9,10,11,14,15,18],newton:[1,24],nft:[1,14],nft_constant_product:[1,21,23],none:[1,13,14,18,19,23],normal:[1,14,19,25],note:[1,13,14,21,25],now:11,num_byte_slic:18,num_uint:18,number:[1,13,24],numer:[1,22],object:[1,11,13,14,15,16,18,19,21,22,23,24,25,26,27],offset:[1,12],old:[1,8,21],omit:[1,12],one:[1,13,19,21,22,23,27],onli:[1,18,19,21,25,27],oper:[1,11,19,21,24],operationtyp:[1,21],opt:[1,2,4,5,9,10,11,13,19],opt_in:11,opt_in_tx:[4,11],opt_in_txn:[2,9,10],optin:[2,10],option:[1,12,13,14,18,19,21,23],order:[1,11,21],origin:[1,19],original_asset:[1,5,19],original_asset_to_f_asset:[1,19],other:[1,19,21,22],other_asset:[1,13],other_coin:[1,11,14],other_pool:[1,21],otherwis:[1,13,18,21,22,25],out:[1,11,13,27],overrid:[1,19],overwrit:[1,14],own:11,packag:[0,11],pact:[1,2,3,4,5,6,8,9,10,12,13,14,18,19,21,23],pact_api_url:[1,12,21],pact_fee_bp:[1,16,23,24,27],pact_pool:[1,5,14,19],pactclient:[1,2,3,4,5,6,8,9,10,11,13,14,21],pactfarmingcli:[1,14],pactfi:11,pactsdk:[2,3,4,5,6,8,9,10,11,12,13,14,15,16,17,18,19,21,22,23,24,25,26,27],pactsdkerror:[1,17,21,24,26],page:11,pagin:[1,12,14],pair:11,param:[1,3,12,14,18,27],paramet:[1,11,12,13,14,18,21,22,23,24,25,26,27],pars:[1,19,21],parse_global_factory_st:18,parse_global_pool_st:[1,23],parse_internal_st:[1,21],particular:[1,25,27],pass:[1,12,13,14,21,26],paus:[1,21],per:[1,21,26],percent:[1,21,22],percentag:[1,25],perform:[1,4,5,9,10,21,25,27],period:11,pip:11,pk:5,place:[1,13],plp:[1,27],plp_opt_in_txn:10,poetri:11,point:[1,13,14,21],pool:[0,2,4,7,9,10,11,12,13,14,16,18,19,20,22,23,24,25,27],pool_asset:[1,12],pool_build_param:[3,5,18],pool_calcul:[0,11,20],pool_param:[3,8,18],pool_stat:[0,11,20,21],pool_typ:[1,18,21],pool_vers:18,poolbuildparam:[3,5,18],poolcalcul:[1,22],poolfactori:18,poolparam:18,poolstat:[1,11,21,23],post_remove_liquid:[1,19],pprint:8,pre_add_liquid:[1,19],precis:[1,13,19,23,24],prepar:[1,21],prepare_:11,prepare_add_liq:[1,27],prepare_add_liquid:[1,2,4,5,11,19,21],prepare_add_liquidity_tx_group:[1,5,19,21],prepare_opt_in_to_asset_tx_group:[1,5,19],prepare_opt_in_tx:[1,2,4,9,10,11,13],prepare_opt_out_tx:[1,13],prepare_remove_liquidity_tx_group:[1,5,11,19,21],prepare_swap:[1,5,9,11,19,21,25],prepare_swap_tx_group:[1,5,11,19,21],prepare_tx_group:[1,2,9,10,11,25,27],prepare_zap:[1,10,21,27],prepare_zap_tx_group:[1,21],price:[1,11,22,24,25],primari:[1,14,19,21,22],primary_add_liq:[1,27],primary_asset:[1,11,12,14,21],primary_asset__algoid:[1,12],primary_asset__nam:[1,12],primary_asset__unit_nam:[1,12],primary_asset_amount:[1,2,4,11,19,21,22],primary_asset_amount_decim:[1,22],primary_asset_id:[3,5,18],primary_asset_index:[1,21],primary_asset_pric:[1,11,22,23],primary_asset_price_after_swap:[1,11,25],primary_asset_price_change_pct:[1,11,25],primary_fe:[1,23],primary_folks_pool:5,primary_lending_pool:[1,5,14,19],primary_liq_chang:[1,22],print:[2,3,4,5,6,8,9,10,11],privat:[1,26],private_kei:[1,2,3,4,8,9,10,11,26],process:[1,14],product:[1,8,14,16,21,27],proper:[1,21],properti:[1,13,21,22,24,26],protocol:[1,11,22],provid:[1,11,14,19,21,22],put:[1,26],py:11,pytest:11,queri:[1,12,13,21],rais:[1,14,21,26],raphson:[1,24],ratio:[1,13],raw_stat:[1,18,23],re:[1,21],read:[1,6,18,21],readi:[1,13,25,27],receiv:[1,13,19,21,22,25],recommend:[1,21],regardless:11,relat:[1,22],relev:[1,14],remliq:[1,21],remov:[1,5,11,19,21],remove_liq_tx_group:11,remove_liquid:[1,19],repres:[1,21,25,27],represent:[1,13,19,23],requir:[1,8,11,21,24],respons:[1,12],result:[1,12,14,19],retri:[1,24],retriev:[1,11,14,18,23],round:[1,27],s:[1,11,14,18,21,22,23,25],same:[1,18,24],satisfi:[1,21],save_iter:[1,24],sdk:[1,13,14,19,24,26],search:11,second:[1,18,21,27],secondari:[1,14,19,21,22],secondary_add_liq:[1,27],secondary_asset:[1,11,12,14,21],secondary_asset__algoid:[1,12],secondary_asset__nam:[1,12],secondary_asset__unit_nam:[1,12],secondary_asset_amount:[1,2,4,11,19,21,22],secondary_asset_amount_decim:[1,22],secondary_asset_id:[3,5,18],secondary_asset_index:[1,21],secondary_asset_pric:[1,11,22,23],secondary_asset_price_after_swap:[1,11,25],secondary_asset_price_change_pct:[1,11,25],secondary_fe:[1,23],secondary_folks_pool:5,secondary_lending_pool:[1,5,14,19],secondary_liq_chang:[1,22],see:[1,13,14,21],select:8,send:[1,11,13,18],send_transact:[2,4,5,9,10,11],sender:[1,3,5,13,18],sent_optin_txid:[2,9,10],sent_plp_optin_txid:10,separ:18,serv:18,set:[1,11,21,22,25,27],should:[1,13,19,27],si:[1,23],side:[1,25],sign:[1,2,3,4,5,9,10,11,18,25,26,27],sign_txn:11,signed_add_liq_tx_group:11,signed_group:[4,9,10],signed_remove_liq_tx_group:11,signed_tx:11,signed_tx_group:[2,11],signedtransact:[1,18,26],signer:[3,5,18],simul:[1,22,24],singl:[1,4,18,22,24,27],size:18,slippag:[1,19,21,22,24,25,27],slippage_pct:[1,5,9,10,11,19,21,22,25,27],smart:[1,24],so:[1,11,13],softwar:11,some:[1,19,21,27],sort:[1,5,22],sp:18,specif:[1,19],specifi:[1,3,11,18,24],speed:[1,13],sqrt:[1,21],stableswap:[1,21,23,24,25,27],stableswap_calcul:[0,11,20],stableswap_param:[1,24],stableswapcalcul:[1,24],stableswapparam:[1,24],stale:[1,21],standard:[1,13,14],state:[1,7,11,18,19,21,23],statist:[1,22],store:[1,18,26],str:[1,12,13,15,18,19,21,23,25,26,27],string:[1,26],submit:11,submodul:0,suggest:[1,11,13,21],suggested_param:[1,4,13,19,21],suggestedparam:[1,13,21],support:[1,13,25],suppos:[1,21,22],swap:[0,5,7,11,13,19,20,21,22,24,27],swap_deposit:[1,27],swap_for_exact:[1,19,21,25],swap_invariant_iter:[1,24],swap_tx_group:[9,11],swapcalcul:[1,22],swapeffect:[1,11,25],system:[1,19],t:[1,3,11,13,18,19,21,25,27],test:[1,19],testb:11,testnet:[1,2,3,4,5,6,8,9,10,11,14],than:[1,14,21],them:[1,22,25,27],thi:[1,2,3,4,5,6,8,9,10,11,12,13,14,18,19,21,22,24,25,26,27],thing:11,those:[1,11,19,21,27],three:[1,21],through:[1,13],throughout:[1,17],thrown:[1,17],time:[1,13,19,25],timestamp:[1,19,24],to_box_nam:18,to_private_kei:[2,3,4,5,8,9,10,11],token:[1,2,3,4,5,6,8,9,10,11,13,14,19,21,22,24,27],too:[1,21],top:11,total:[1,22,24],total_amount:[1,12,27],total_liquid:[1,11,16,23,24],total_primari:[1,11,16,23,24,27],total_secondari:[1,11,16,23,24,27],trade:[1,11,19,21,25,27],transact:[1,2,7,9,10,13,18,19,21,24,25,26,27],transaction_group:[0,11,20,21],transactiongroup:[1,4,11,18,19,21,25,26,27],transfer:[1,19],treasuri:[1,23],tri:[1,19],trust:18,tupl:[1,13,18,22,24],tvl_usd:[1,12],two:[1,11,14,18,19,21],tx:[1,4,21,24],tx_fee:[1,19,25],tx_group:[3,5],type:[1,8,12,13,14,15,16,18,19,21,22,23,24,25,26,27],typeddict:[1,12],typic:[1,13,14,21,25,27],unbalanc:[1,24],union:[1,14,21],uniqu:18,unit:[1,13,19],unit_nam:[1,12,13],unlimit:18,up:[1,11,13],updat:[1,11,21],update_st:[1,11,21],updated_at:[1,19],updated_tot:[1,24],url:[1,2,3,4,5,6,8,9,10,11,12,14,21],us:[1,8,11,13,14,17,18,19,21,22,24,25,26,27],usag:[1,14],usdc:[1,2,4,5,6,9,10,19],user:[1,19,21,22,23,25,27],util:[1,13,25,27],v1:11,v2client:[1,2,3,4,5,6,8,9,10,11,13,14,18,19,21],valid:[1,11,14,18],valu:[1,11,13,14,19,21,22,24],versa:[1,21],version:[1,11,18,21,23],vice:[1,21],volume_24h:[1,12],volume_7d:[1,12],wa:[1,21,26],wai:[1,11,14,22],want:[1,11,13,22,25],we:[1,24],what:[1,11,25],when:[1,13,19,21,22,25,27],which:[1,11,14,21,22,27],whl:11,withdrawn:[1,21],within:[1,17,21],without:[1,13,18],work:[1,11,14,18,21,25,27],wrapper:[1,19],yet:[1,3,18,22],you:[1,11,13,14,18,21,25],your:11,zap:[0,7,11,20,21],zap_amount:[1,27],zap_tx_group:10,zapparam:[1,27],zero:[1,14,21,22,24,25]},titles:["pactsdk","pactsdk package","Add liquidity","Build pool","Composing transactions","Folks lending pool","Get pool state","Examples","List pools","Swap","Zap","Pact Python SDK","api","asset","client","config","constant_product_calculator","exceptions","factories","folks_lending_pool","pactsdk","pool","pool_calculator","pool_state","stableswap_calculator","swap","transaction_group","zap"],titleterms:{add:2,api:[1,12],asset:[1,13],basic:11,build:[3,11],client:[1,14],compos:[4,11],config:[1,15],constant_product_calcul:[1,16],content:[1,11],develop:11,exampl:7,except:[1,17],factori:[1,18],folk:5,folks_lending_pool:[1,19],get:6,indic:11,instal:11,lend:5,liquid:2,list:[8,11],modul:1,packag:1,pact:11,pactsdk:[0,1,20],pool:[1,3,5,6,8,21],pool_calcul:[1,22],pool_stat:[1,23],python:11,run:11,sdk:11,stableswap_calcul:[1,24],state:6,submodul:1,swap:[1,9,25],tabl:11,test:11,transact:[4,11],transaction_group:[1,26],usag:11,zap:[1,10,27]}})