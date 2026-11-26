// Player hats (bm_hats.qc)
.float	bm_hat;			// the hat this client picked, 0 for none (sent with "cmd bm_hat N")
.entity	bm_hat_ent;		// the hat riding on the player's head

void() BM_Hats_Precache;
void() BM_Hat_Update;
void(entity p) BM_Hat_Clear;
void(string s) BM_Hat_Command;
