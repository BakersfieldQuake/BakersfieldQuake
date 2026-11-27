// Player hats (bm_hats.qc)
.float	bm_hat;			// the hat this client picked, 0 for none (sent with "cmd bm_hat N")
.entity	bm_hat_ent;		// the hat riding on the player's head
.float	bm_hat_lastpf;	// cached player frame last applied to attached hat offset/angles
.float	bm_hat_lastaf;	// cached hat animation frame last applied

void() BM_Hats_Precache;
void() BM_Hat_Update;
void(entity p) BM_Hat_Clear;
void(string s) BM_Hat_Command;
