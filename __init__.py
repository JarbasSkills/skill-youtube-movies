from os.path import join, dirname

from ovos_plugin_common_play.ocp import MediaType, PlaybackType
from ovos_utils.parse import fuzzy_match, MatchStrategy
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill, \
    ocp_search
from tutubo import YoutubeSearch
from tutubo.models import *


class YoutubeFullMoviesSkill(OVOSCommonPlaybackSkill):
    def __init__(self):
        super(YoutubeFullMoviesSkill, self).__init__("YoutubeFullMovies")
        self.supported_media = [MediaType.GENERIC, MediaType.MOVIE]
        self.skill_icon = join(dirname(__file__), "ui", "logo.png")

    # score
    def calc_score(self, phrase, match, idx=0, base_score=0):
        if self.voc_match(match.title, "full_movie"):
            return 0
        # idx represents the order from youtube
        score = base_score - idx  # - 1% as we go down the results list
        score += 100 * fuzzy_match(phrase.lower(), match.title.lower(),
                                   strategy=MatchStrategy.TOKEN_SET_RATIO)
        return min(100, score)

    # common play
    @ocp_search()
    def search_youtube(self, phrase, media_type):
        base_score = 0
        if self.voc_match(phrase, "full_movie"):
            base_score += 10
            phrase = self.remove_voc(phrase, "full_movie")
        elif self.voc_match(phrase, "movie"):
            base_score += 5
            phrase = self.remove_voc(phrase, "movie")
        elif media_type != MediaType.MOVIE:
            # only search db if user explicitly requested movies
            return

        if self.voc_match(phrase, "youtube"):
            # explicitly requested youtube
            base_score += 40
            phrase = self.remove_voc(phrase, "youtube")

        idx = 0
        for v in YoutubeSearch(phrase + " full movie").iterate_youtube(
                max_res=10):
            if isinstance(v, Video) or isinstance(v, VideoPreview):
                if v.length < 3600:
                    continue  # not a full movie if len < 1 hour
                score = self.calc_score(phrase, v, idx, base_score=base_score)
                if score < 50:
                    continue
                # return as a video result (single track dict)
                yield {
                    "match_confidence": score,
                    "media_type": MediaType.MOVIE,
                    "length": v.length * 1000,
                    "uri": "youtube//" + v.watch_url,
                    "playback": PlaybackType.VIDEO,
                    "image": v.thumbnail_url,
                    "bg_image": v.thumbnail_url,
                    "skill_icon": self.skill_icon,
                    "title": v.title,
                    "skill_id": self.skill_id
                }
                idx += 1
            else:
                continue


def create_skill():
    return YoutubeFullMoviesSkill()
