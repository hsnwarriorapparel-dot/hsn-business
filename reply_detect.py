"""Reply detection for the outreach sweep.

A buyer reply does not have to be in English. Shudokan (Spain) replied
"¿podrías enviarme catálogo y listado de precios?" and the sweep reported
0 human replies because every hint word was English.

A gmail thread line looks like:

    <sender> :: [unread, ]me, SUBJECT, TIME, REPLY_SNIPPET, QUOTED_OUR_MSG

The reply snippet comes BEFORE the quote of our own message. So the rule is:
split at the quote marker, and look only at what comes before it.

Pure functions, no side effects - so they can be unit tested.
"""
import re

# ---------------------------------------------------------------- the hints --
# Interest words, in every language the leads actually write in.
HUMAN_HINT = re.compile(
    r'we (are|would) (like|be interested)|interested in|quotation|quote|price list|'
    r'catalog|how much|minimum order|\bmoq\b|sample|please send|'
    r'could you send|can you send|can you share|would like to know|'
    r'we want to (buy|order)|we are looking for|'
    # Spanish
    r'cat[aá]logo|lista de precios|listado de precios|estar[ií]a interesado|'
    r'nos gustar[ií]a|presupuesto|cotizaci[oó]n|qu[eé] tal|'
    r'precio de|nos env[ií]a|env[ií]ame|interesados en|'
    # Portuguese
    r'cat[aá]logo|lista de pre[cç]os|or[çc]amento|tenho interesse|'
    r'gostaria de saber|seria interessante|podem enviar|'
    # German
    r'interesse an|bitte senden|ich w[uü]rde gerne|k[oö]nnten sie|'
    # Italian / Spanish-Italian
    r'mi interessa|potrei ricevere|sarebbe possibile|possiamo ricevere|'
    # Dutch
    r'geïnteresseerd|graag ontvangen|kunt u ons|'
    # Polish
    r'prosz[eę] o (katalog|cenownik)|interesuj[eę] nas|'
    # Turkish
    r'fiyat listesi|katalog|merhaba|'
    # Arabic transliteration
    r'الأسعار|كتالوج', re.I)

# ------------------------------------------------------------- the excludes --
# The buyer is not interested - never count as a human reply.
NOT_INTERESTED = re.compile(
    r'not interested|no estoy interesad[oa]|no estoy interesad[oa]|'
    r'pas d.int[ée]r[eê]t|nicht interessiert|kein interesse|'
    r'nie jestem zainteresowan|non sono interessat|'
    r'n[ãa]o tenho interesse', re.I)

# An auto-responder or a forwarder - a human is not on the other end yet.
FORWARD_NOISE = re.compile(
    r'we.ve forwarded|we have forwarded|forwarded your message to|'
    r'we.ve passed (it|your)|przekazali[śs]my|'
    r'ersuche ich (Sie|ihre) (ihre )?anliegen an|'
    r'the relevant team|if there.s any interest|'
    r'i will endeavour to respond|thank you for your email\.? i will|'
    r'we.ll get back to you|we will respond', re.I)

# Out-of-office / vacation.
OOO = re.compile(
    r'will be away|out of office|auto[- ]?reply|automatic reply|'
    r'not be able to respond until|we are preparing for', re.I)

# A plain thank-you acknowledgement with no interest in it.
ACK_ONLY = re.compile(
    r'^\s*(thanks?|thank you|danke|gracias|obrigad[oa]|dzi[eę]kujemy|'
    r'merhaba|merci)\b[\s,.!]*$', re.I)

# ------------------------------------------------------------- our own mail --
# Our own address as the sender of a message inside the thread.
OUR_OWN_MSG = re.compile(
    r'hsnwarriorapparel@gmail\.com\s*::\s*me,|'
    r'\bme,\s*(Custom martial arts gear|Branded uniforms|Custom gear|'
    r'Hot |New |SHUDOKAN|Fight |Zuziboxing|Mail \d|Custom |Factory|'
    r'We are HSN|Your email Submission)', re.I)

# The marker that starts the QUOTE of our own message inside the reply.
QUOTE_MARK = re.compile(
    r'(HSN\s*\(\s*<hsnwarriorapparel@gmail\.com>\s*\)\s*(escribi[oó]|wrote)|'
    r'HSN\s*<hsnwarriorapparel@gmail\.com>\s*(wrote|escribi[oó]|a [eé]crit)|'
    r'On\s.{0,60}?\bHSN\b.{0,30}?\bwrote:|'
    r'--------\s*Original Message|^\s*me,\s)', re.I | re.M)

# Notification / system senders.
NOISE_SENDER = re.compile(
    r'(mailer-daemon|postmaster|noreply|no-reply|donotreply|'
    r'notifications@|facebook|instagram|google\.com|'
    r'go4worldbusiness|tradewheel|cjdropship|sentry\.|wixpress|'
    r'@.*\.gov)', re.I)

# Subjects that are never a buyer reply.
NOISE_SUBJ = re.compile(
    r'(Delivery incomplete|Address not found|Message not delivered|'
    r'Undelivered Mail|Message blocked|Invitation:|Your Inquiry Sent|'
    r'FW: WANTED|Reminder|automatic reply)', re.I)


def detect_reply(line):
    """Return (snippet, reason). snippet is None when it is not a human reply."""
    if not line:
        return None, 'empty'
    if NOISE_SUBJ.search(line):
        return None, 'noise-subject'
    if NOISE_SENDER.search(line):
        return None, 'noise-sender'

    # THE QUOTE MARKER IS THE KEY.
    #
    # Gmail renders a thread line as:
    #     <span-sender> :: <flags> <subject> <time> <NEWEST MESSAGE BODY>
    #
    # When somebody replied to us, their message quotes ours at the end:
    #     Buenos dias, podrias enviarme catalogo ... Un saludo
    #     El mie, 14 oct 2026 a las 21:14, HSN (<...>) escribio:
    #     <- everything after this marker is OUR quoted message
    #
    # So: text BEFORE the marker = the reply. Text after = our own copy.
    # No marker at all = the line IS our own message.
    q = QUOTE_MARK.search(line)
    head = line[:q.start()] if q else line

    if not head.strip():
        return None, 'nothing-before-quote'
    # The SENDER of the reply is the part BEFORE the first '::'.
    # A line can start with our own address (because Gmail shows the thread
    # as "hsnwarriorapparel@gmail.com :: me, SUBJECT, <reply>") and still
    # contain a real reply further along. So only the sender span decides
    # who wrote it - not the whole line.
    # The thread line is a sequence of MESSAGE SPANS:
    #     <sender> :: [flags] <subject> <time> <body>
    # A reply from a buyer has ITS OWN sender span. If the only sender span
    # is our own address, the whole thing is our outbound message.
    # A thread line can hold two messages: ours and the buyer's.
    #
    #   hsnwarriorapparel@gmail.com :: me, SUBJ, 1:19 PM, <REPLY> ...
    #
    # The buyer replied AFTER our message. So the rule is simple and
    # reliable: if the line mentions a sender that is NOT us, it is a
    # thread that contains somebody else's message.
    #
    #   'hsnwarriorapparel@gmail.com :: me, ...'  -> only us
    #   'info@club.com :: unread, ...'            -> somebody else
    #   'shudokan.roje@gmail.com :: ...'          -> somebody else
    if q is None:
        # No quote of our message anywhere in the line, and the line does
        # not come from somebody else -> it is our own outbound message.
        senders = re.findall(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)\s*::', head)
        senders = [s.lower() for s in senders]
        others = [s for s in senders if s != 'hsnwarriorapparel@gmail.com']
        if not others:
            return None, 'our-own-message'
    if NOT_INTERESTED.search(head):
        return None, 'not-interested'
    if OOO.search(head):
        return None, 'out-of-office'
    if FORWARD_NOISE.search(head):
        return None, 'forwarded/no-human'
    if ACK_ONLY.match(head.split('::')[-1].strip()):
        return None, 'ack-only'
    if not HUMAN_HINT.search(head):
        return None, 'no-hint'

    # The snippet we report: the part of the head after the timestamp.
    snip = head
    m = re.search(r'\d{1,2}:\d{2}\s*[AP]M', head)
    if m:
        snip = head[m.end():]
    return snip.strip()[:240] or head.strip()[:240], 'HUMAN'
