// Compiled inside a separately retained copy of the pinned KataGo tree.
// No model, search, inferred outcome labels, or Python Go rules are involved.
#include "dataio/sgf.h"
#include "external/nlohmann_json/json.hpp"
#include <iostream>
#include <regex>

using nlohmann::json;

static json replay(const std::string& text) {
  auto sgf = Sgf::parse(text); // Build patch requires complete input consumption.
  const auto& root = *sgf->nodes.at(0);
  if(!root.hasProperty("SZ") || sgf->getXYSize().x != 19 || sgf->getXYSize().y != 19)
    throw StringError("board-size");
  if(root.hasProperty("GM") && root.getSingleProperty("GM") != "1")
    throw StringError("not-go");
  Rules rules = sgf->getRulesOrFail();
  rules.komi = sgf->getKomiOrFail();
  Rules required = Rules::parseRules("chinese");
  required.komi = 7.5f;
  if(rules != required) throw StringError("rules-or-komi");
  if(sgf->getHandicapValue() != 0) throw StringError("handicap");
  if(root.hasProperty("PL") && root.getPLSpecifiedColor() != P_BLACK)
    throw StringError("initial-player");
  const std::string comment = root.getSingleProperty("C");
  std::map<std::string,std::string> origin;
  const std::regex field("(?:^|,)(startTurnIdx|initTurnNum|gameHash|gtype|usedInitialPosition|beganInEncorePhase)=([^,\\s]+)");
  for(auto i = std::sregex_iterator(comment.begin(),comment.end(),field); i != std::sregex_iterator(); ++i) {
    if(!origin.emplace((*i)[1].str(),(*i)[2].str()).second)
      throw StringError("ambiguous-origin");
  }
  if(origin["gtype"].empty() || origin["initTurnNum"] != "0" ||
     !std::regex_match(origin["gameHash"],std::regex("[0-9a-fA-F]{32}")) ||
     !std::regex_match(origin["startTurnIdx"],std::regex("[0-9]+")) ||
     (origin.count("beganInEncorePhase") && origin["beganInEncorePhase"] != "0"))
    throw StringError("unknown-or-nonordinary-origin");
  Board board(19,19);
  BoardHistory hist(board,P_BLACK,rules,0,BoardHistoryModes(false,false));
  json moves = json::array(), states = json::array();
  bool isRoot = true;
  for(const Sgf* branch = sgf.get(); branch != nullptr;
      branch = branch->children.empty() ? nullptr : branch->children.front().get()) {
    for(const auto& node : branch->nodes) {
      if(node->hasPlacements()) throw StringError("setup-or-edited-position");
      if(!isRoot) {
        for(const char* key : {"PL","SZ","RU","KM","HA"})
          if(node->hasProperty(key)) throw StringError("mid-history-metadata-edit");
      }
      std::vector<Move> nodeMoves;
      node->accumMoves(nodeMoves,19,19);
      if(nodeMoves.size() > 1) throw StringError("multiple-moves-in-node");
      isRoot = false;
      for(const Move& move : nodeMoves) {
        if(hist.isGameFinished) throw StringError("post-terminal-move");
        if(!hist.isLegal(board,move.loc,move.pla)) throw StringError("illegal-move");
        std::string stones;
        bool atari = false;
        for(int y = 0; y < 19; y++) for(int x = 0; x < 19; x++) {
          Loc loc = Location::getLoc(x,y,19);
          Color c = board.colors[loc];
          stones += c == P_BLACK ? 'B' : c == P_WHITE ? 'W' : '.';
          if(c != C_EMPTY && board.getNumLiberties(loc) == 1) atari = true;
        }
        states.push_back({{"terminal",false},{"phase",hist.encorePhase},
          {"next_player",move.pla == P_BLACK ? "B" : "W"}, {"stones",stones},
          {"atari",atari}, {"ko",board.ko_loc != Board::NULL_LOC},
          {"single_pass",hist.consecutiveEndingPasses == 1}});
        json coordinate = nullptr;
        if(move.loc != Board::PASS_LOC)
          coordinate = {Location::getX(move.loc,19),Location::getY(move.loc,19)};
        moves.push_back({move.pla == P_BLACK ? "B" : "W",coordinate});
        hist.makeBoardMoveAssumeLegal(board,move.loc,move.pla,nullptr);
      }
    }
  }
  if(moves.empty() || std::stoull(origin["startTurnIdx"]) > moves.size())
    throw StringError("inconsistent-origin-history");
  return {{"status",origin["gtype"] == "normal" && (!origin.count("usedInitialPosition") || origin["usedInitialPosition"] == "0") ? "admitted" : "lineage_required"}, {"rules",rules.toJsonNoKomi()}, {"komi",7.5},
    {"initial_player","B"}, {"origin",origin}, {"moves",moves}, {"states",states},
    {"endpoint",{{"terminal",hist.isGameFinished},{"no_result",hist.isNoResult},
      {"two_pass",hist.consecutiveEndingPasses >= 2}}},
    {"recorded_result",sgf->getRootPropertyWithDefault("RE","")}};
}

int astragoAdmission(const std::vector<std::string>&) {
  Board::initHash();
  std::string line;
  while(std::getline(std::cin,line)) {
    json result;
    try { result = replay(json::parse(line).at("sgf").get<std::string>()); }
    catch(const std::exception& error) { result = {{"status","excluded"},{"reason",error.what()}}; }
    result["schema"] = "astrago-native-admission-v1";
    result["history_modes"] = {false,false};
    std::cout << result.dump() << std::endl;
  }
  return 0;
}
