#pragma version 8

struct Assets:
    original_asset: int
    f_asset: int
end

struct InterestInfo:
    reserved: bytes[32]
    interest_rate: int
    interest_index: int
    updated_at: int
end

# deposit(txn,account,asset,asset,application)uint64
const bytes DEPOSIT_SIG = "\xb9\xd5B\xfb"

# withdraw(axfer,uint64,account,asset,asset,application)uint64
const bytes WITHDRAW_SIG = "\xea\xbe\x82\x9d"

const int SECONDS_IN_YEAR = 31536000
const int ONE_14_DP = 100000000000000
const int ONE_16_DP = 10000000000000000

if Txn.ApplicationID == 0:
    exit(1)
end

switch Txn.OnCompletion:
    NoOp: main
end

block main:
    switch Txn.ApplicationArgs[0]:
        "init": init
        DEPOSIT_SIG: deposit
        WITHDRAW_SIG: withdraw
    end

    block init:
        # Not present in original contract. Added for easier testing.
        init()
        exit(1)
    end

    block deposit:
        deposit()
        exit(1)
    end

    block withdraw:
        withdraw()
        exit(1)
    end
end

func init():
    # Args: [
    #    1: manager_app: int
    #    2: interest_rate: int
    #    3: interest_index: int
    #    4: updated_at: int
    # ]
    # Assets: [
    #    0: original_asset
    # ]

    app_global_put("pm", Txn.ApplicationArgs[1])

    int original_asset
    if Txn.NumAssets == 0:
        # Algo
        original_asset = 0
    else:
        original_asset = Txn.Assets[0]
        opt_in_asset(original_asset)
    end

    Assets assets = bzero(16)
    assets.original_asset = original_asset
    assets.f_asset = create_f_asset(original_asset)
    app_global_put("a", assets)

    InterestInfo interest_info = bzero(56)
    interest_info.interest_rate = btoi(Txn.ApplicationArgs[2])
    interest_info.interest_index = btoi(Txn.ApplicationArgs[3])
    interest_info.updated_at = btoi(Txn.ApplicationArgs[4])
    app_global_put("i", interest_info)


    return
end

func create_f_asset(asset: int) int:
    bytes unit_name
    bytes name
    int decimals
    int total

    if asset == 0:
        unit_name = 'fALGO'
        name = 'Folks Algo'
        total = 10000000000
        decimals = 6
    else:
        int exists
        exists, unit_name = asset_params_get(AssetUnitName, asset)
        exists, name = asset_params_get(AssetName, asset)
        exists, decimals = asset_params_get(AssetDecimals, asset)
        exists, total = asset_params_get(AssetTotal, asset)

        unit_name = concat("f", unit_name)
        name = concat("Folks ", name)
    end

    inner_txn:
        TypeEnum: Acfg
        Sender: Global.CurrentApplicationAddress
        ConfigAssetUnitName: unit_name
        ConfigAssetName: name
        ConfigAssetTotal: total
        ConfigAssetDecimals: decimals
    end

    return Itxn.CreatedAssetID
end

func opt_in_asset(asset: int):
    inner_txn:
        TypeEnum: Axfer
        Sender: Global.CurrentApplicationAddress
        AssetReceiver: Global.CurrentApplicationAddress
        XferAsset: asset
        AssetAmount: 0
    end
    return
end

func deposit():
    int deposited
    Assets assets = app_global_get("a")
    if assets.original_asset == 0:
        assert(Gtxn[-1].TypeEnum == Pay)
        assert(Gtxn[-1].Receiver == Global.CurrentApplicationAddress)
        deposited = Gtxn[-1].Amount
    else:
        assert(Gtxn[-1].TypeEnum == Axfer)
        assert(Gtxn[-1].XferAsset == assets.original_asset)
        assert(Gtxn[-1].AssetReceiver == Global.CurrentApplicationAddress)
        deposited = Gtxn[-1].AssetAmount
    end

    inner_txn:
        TypeEnum: Axfer
        Sender: Global.CurrentApplicationAddress
        AssetReceiver: Txn.Sender
        XferAsset: assets.f_asset
        AssetAmount: convert_deposit(deposited)
    end

    make_empty_manager_call()

    return
end

func withdraw():
    Assets assets = app_global_get("a")
    assert(Gtxn[-1].TypeEnum == Axfer)
    assert(Gtxn[-1].XferAsset == assets.f_asset)
    assert(Gtxn[-1].AssetReceiver == Global.CurrentApplicationAddress)

    int withdrawed = Gtxn[-1].AssetAmount

    if assets.original_asset == 0:
        inner_txn:
            TypeEnum: Pay
            Sender: Global.CurrentApplicationAddress
            Receiver: Txn.Sender
            Amount: convert_withdraw(withdrawed)
        end
    else:
        inner_txn:
            TypeEnum: Axfer
            Sender: Global.CurrentApplicationAddress
            AssetReceiver: Txn.Sender
            XferAsset: assets.original_asset
            AssetAmount: convert_withdraw(withdrawed)
        end
    end

    make_empty_manager_call()

    # In the real code it's the manager who sends the money back to the user, so here we add an empty transaction to simulate the transaction fee increase.
    inner_txn:
        TypeEnum: Axfer
        Sender: Global.CurrentApplicationAddress
        AssetReceiver: Txn.Sender
        XferAsset: assets.f_asset
        AssetAmount: 0
    end

    return
end

func make_empty_manager_call():
    inner_txn:
        TypeEnum: Appl
        OnCompletion: NoOp
        Sender: Global.CurrentApplicationAddress
        ApplicationID: btoi(app_global_get('pm'))
    end

    return
end

func convert_deposit(amount: int) int:
    int rate = calc_deposit_interest_index()
    return btoi((itob(amount) b* itob(ONE_14_DP)) b/ itob(rate))
end

func convert_withdraw(amount: int) int:
    int rate = calc_deposit_interest_index()
    return btoi((itob(amount) b* itob(rate)) b/ itob(ONE_14_DP))
end

func calc_deposit_interest_index() int:
    InterestInfo interest_info = app_global_get("i")
    # Using Round instead of LatestTimestamp for easier testing.
    bytes dt = itob(Global.Round - interest_info.updated_at)

    bytes xx = itob(ONE_16_DP) b+ ((itob(interest_info.interest_rate) b* dt) b/ itob(SECONDS_IN_YEAR))

    bytes yy = (itob(interest_info.interest_index) b* xx) b/ itob(ONE_16_DP)

    return btoi(yy)
end
