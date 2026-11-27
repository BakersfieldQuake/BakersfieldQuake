/*
================
bm_console.qc — Sleek colorized console, chat (T / Y), and notification formatting

Intercepts incoming server prints via Zircon's CSQC_Parse_Print(string msg):
  - Formats chat messages with high-contrast sky-cyan / emerald speaker tags & crisp white text
  - Preserves leading char 1 / 3 chat markers via str2chr/chr2str so CON_MASK_CHAT and chat sounds work
  - Color-codes uncolored system, bot, kill, pickup, join/leave, and warning lines
================
*/

float(string hay, string needle) BM_ConHas =
{
	local float idx;

	idx = strstrofs (hay, needle);
	return (idx >= 0);
};

string(string msg, float ch0) BM_ColorizeChatLine =
{
	local string pfx, rest, name, body;
	local float colon, close_ang;

	pfx = chr2str (ch0);
	rest = substring (msg, 1, strlen (msg) - 1);

	// Team chat: "(Name): message"
	if (substring (rest, 0, 1) == "(")
	{
		colon = strstrofs (rest, "): ");
		if (colon > 1)
		{
			name = substring (rest, 0, colon + 1);
			body = substring (rest, colon + 3, strlen (rest) - (colon + 3));
			return strcat (pfx, "^2", name, "^9: ^xBF9", body);
		}
	}

	// Server broadcast chat: "<Server> message"
	if (substring (rest, 0, 1) == "<")
	{
		close_ang = strstrofs (rest, "> ");
		if (close_ang > 1)
		{
			name = substring (rest, 0, close_ang + 1);
			body = substring (rest, close_ang + 2, strlen (rest) - (close_ang + 2));
			return strcat (pfx, "^3", name, " ^7", body);
		}
	}

	// Standard player chat: "Name: message"
	colon = strstrofs (rest, ": ");
	if (colon > 0)
	{
		name = substring (rest, 0, colon);
		body = substring (rest, colon + 2, strlen (rest) - (colon + 2));
		return strcat (pfx, "^5", name, "^9: ^7", body);
	}

	return strcat (pfx, "^7", rest);
};

string(string msg) BM_ColorizeSystemLine =
{
	local string low, lead;
	local float pos;

	// Leave strings that already carry Quake color codes untouched
	if (BM_ConHas (msg, "^"))
		return msg;

	lead = substring (msg, 0, 1);
	if (lead == "\n")
		return msg;

	low = strtolower (msg);

	if (BM_ConHas (low, "error") || BM_ConHas (low, "failed") || BM_ConHas (low, "warning"))
		return strcat ("^1", msg);

	if (BM_ConHas (low, "entered the game"))
	{
		pos = strstrofs (msg, " entered the game");
		if (pos > 0)
			return strcat ("^2+ ^5", substring (msg, 0, pos), "^2", substring (msg, pos, strlen (msg) - pos));
		return strcat ("^2", msg);
	}

	if (BM_ConHas (low, "left the game"))
	{
		pos = strstrofs (msg, " left the game");
		if (pos > 0)
			return strcat ("^1- ^5", substring (msg, 0, pos), "^9", substring (msg, pos, strlen (msg) - pos));
		return strcat ("^9", msg);
	}

	if (substring (msg, 0, 8) == "You got ")
		return strcat ("^2You got ^3", substring (msg, 8, strlen (msg) - 8));

	if (substring (msg, 0, 12) == "You receive ")
		return strcat ("^2You receive ^3", substring (msg, 12, strlen (msg) - 12));

	if (BM_ConHas (msg, "[BOT]"))
		return strcat ("^6", msg);

	if (BM_ConHas (low, "was ") || BM_ConHas (low, "killed") || BM_ConHas (low, "telefragged")
		|| BM_ConHas (low, "blew ") || BM_ConHas (low, "slipped") || BM_ConHas (low, "discharges")
		|| BM_ConHas (low, "melted") || BM_ConHas (low, "fell") || BM_ConHas (low, "squished")
		|| BM_ConHas (low, "eaten") || BM_ConHas (low, "fried") || BM_ConHas (low, "mown down"))
		return strcat ("^xF87", msg);

	if (BM_ConHas (low, "timelimit") || BM_ConHas (low, "fraglimit") || BM_ConHas (low, "map ") || BM_ConHas (low, "vote"))
		return strcat ("^5", msg);

	return strcat ("^7", msg);
};

void(string msg) CSQC_Parse_Print =
{
	local float ch0;

	if (msg == "")
		return;

	ch0 = str2chr (msg, 0);
	if (ch0 == 1 || ch0 == 3)
	{
		print (BM_ColorizeChatLine (msg, ch0));
		return;
	}

	print (BM_ColorizeSystemLine (msg));
};
