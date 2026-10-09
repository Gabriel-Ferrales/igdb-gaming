
``` mermaid
flowchart LR
    subgraph STAGING["Staging"]
        SG[stg_games]
        SGE[stg_genres]
        SP[stg_platforms]
        ST[stg_themes]
        SM[stg_game_modes]
        SIC[stg_involved_companies]
        SC[stg_companies]
        SR[stg_release_dates]
    end

    subgraph INTERMEDIATE["Intermediate"]
        IG[int_game_genres<br/>game_id + genre_id]
        IP[int_game_platforms<br/>game_id + platform_id]
        IT[int_game_themes<br/>game_id + theme_id]
        IM[int_game_modes<br/>game_id + game_mode_id]
        IC[int_game_companies<br/>involved_company_id]
        IR[int_game_releases<br/>release_date_id]
    end

    subgraph MARTS["Future marts"]
        BG[bridge_game_genres]
        BP[bridge_game_platforms]
        BT[bridge_game_themes]
        BM[bridge_game_modes]
        FC[fct_game_companies]
        FR[fct_game_releases]
    end

    SG --> IG
    SGE --> IG

    SG --> IP
    SP --> IP

    SG --> IT
    ST --> IT

    SG --> IM
    SM --> IM

    SIC --> IC
    SC --> IC
    SG --> IC

    SR --> IR
    SG --> IR
    SP --> IR

    IG --> BG
    IP --> BP
    IT --> BT
    IM --> BM
    IC --> FC
    IR --> FR
```