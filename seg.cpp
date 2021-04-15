/*
This is the code for the phrase-level analysis of the paper: Automatic Analysis and Influence of Hierarchical Structure on Melody, Rhythm and Harmony in Popular Music 
https://www.cs.cmu.edu/~rbd/papers/dai-mume2020.pdf

Input: Preprocessing results of a midi song from preprocessing.sh, including melody.txt, finalized_chord.txt, analyzed_key.txt, time signature
Output: Phrase-level structure analysis result

Notice that it is an approximate version, if you want to run the full version, turn off the timing code at line 1822
Author: Shuqi Dai
Oct, 2020
*/

#include <stdio.h>
#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <string>
#include <cstring>
#include <string.h>
#include <algorithm>
#include <vector>
#include <math.h>
#include <cmath>
#include <random>
#include <time.h>
#include <set>
using namespace std;


/* =====================      CLASS Definitions       ====================== */

class Chord {
  public:
      char name[10];
      bool tones[12]; // from pitch C (0) to B (11)
      int bass;
      int duration; // in unit of beat

      Chord(char* name_, int bass_, int duration_, vector<int> tone_) {
          strcpy(name, name_);
          bass = bass_;
          duration = duration_;
          memset(tones, 0, sizeof(tones));
          for (int i = 0; i < tone_.size(); ++i)
              tones[tone_[i]] = 1;
      }
      Chord(const Chord& c) {
          strcpy(name, c.name);
          for (int i = 0; i < 12; ++i)
              tones[i] = c.tones[i];
          bass = c.bass;
          duration = c.duration;
      }
      Chord &operator=(const Chord& c) {
          if (this == &c) {
              return *this;
          }
          strcpy(this->name, c.name);
          this->bass = c.bass;
          this->duration = c.duration;
          for (int i = 0; i < 12; ++i)
              this->tones[i] = c.tones[i];
          return *this;
      }
      void printChord() const {
          printf("%s duration: %d bass: %d (", name, duration, bass);
          for (int k = 0; k < 12; ++k)
             printf("%d, ", tones[k]);
         printf(")\n");
      }
};

class Note {
  public:
      int pitch, duration;
      // pitch is MIDI number, -2 means REST note
      // duration in sixteenth notes

      Note(int pitch_, int duration_) {
          pitch = pitch_;
          duration = duration_;
      }

      Note(const Note& x) {
          pitch = x.pitch;
          duration = x.duration;
      }
      void printNote() const {
          printf(" (%d, %d) ", pitch, duration);
      }
};

// Section class means a fragment of the song
class Section {
  public:
      vector<Note> melody;
      vector<Chord> chords;
      int start, end; // bar number in original piece
      int time_signature; // how many 16th beats are there in each bar, 4/4 - 16, 3/4 -12
      vector<string> key_name;

      Section() {
          melody.clear();
          chords.clear();
          start = end = 0;
          key_name.clear();
          time_signature = 0;
      }
    
      Section(int length, int time_signature_) {
          melody.clear();
          chords.clear();
          start = 0;
          end = length;
          key_name.clear();
          time_signature = time_signature_;
          melody.push_back(Note(-2, (end - start) * time_signature));
       }

      Section(const Section& x) {
          melody = x.melody;
          chords = x.chords;
          start = x.start;
          end = x.end;
          time_signature = x.time_signature;
          key_name = x.key_name;
      }
    
      bool is_same(const Section& x) const {
          if (start == x.start && end == x.end) return 1;
          return 0;
      }
    
      bool non_overlap(const Section& x) const {
          if (start >= x.end || end <= x.start) return 1;
          return 0;
      }
      
      // transpose the whole section to another key
      // notice that, here we do not rewrite the key name or chord name
      // only melody pitch and chord tones are changed
      void transpose_section(int delta) {
          for (int i = 0; i < melody.size(); ++i)
              if (melody[i].pitch > -2) melody[i].pitch += delta;
          for (int i = 0; i < chords.size(); ++i) {
              bool tmp_tones[12];
              for (int j = 0; j < 12; ++j)
                  tmp_tones[(j + delta) % 12] = chords[i].tones[j];
              for (int j = 0; j < 12; ++j)
                  chords[i].tones[j] = tmp_tones[j];
          }
      }
    
      // return a subsection of current section
      Section subsection(int l, int r) const {
          Section sub;
          sub.start = l;
          sub.end = r;
          sub.time_signature = time_signature;
          sub.key_name = key_name;
          int mt = start * time_signature, i = 0;
          while (i < melody.size() && mt + melody[i].duration < l * time_signature) {
              mt = mt + melody[i].duration;
              ++i;
          }
          if (i < melody.size()) {
              Note tmp_melody(melody[i]);
              tmp_melody.duration = mt + melody[i].duration - l * time_signature;
              mt = mt + melody[i].duration;
              ++i;
              if (tmp_melody.duration > 0)
                  sub.melody.push_back(tmp_melody);
              while (i < melody.size() && mt < r * time_signature) {
                  if (mt + melody[i].duration > r * time_signature) {
                      Note tmp_note_again(melody[i]);
                      tmp_note_again.duration = r * time_signature - mt;
                      sub.melody.push_back(tmp_note_again);
                      break;
                  }
                  sub.melody.push_back(Note(melody[i]));
                  mt += melody[i].duration;
                  ++i;
              }
          }

          int t = start * time_signature / 4;
          i = 0;
          while (i < chords.size() && t + chords[i].duration < l * time_signature / 4) {
              t = t + chords[i].duration;
              ++i;
          }
          if (i < chords.size()) {
              Chord tmp_chord(chords[i]);
              tmp_chord.duration = t + chords[i].duration - l * time_signature / 4;
              t = t + chords[i].duration;
              ++i;
              if (tmp_chord.duration > 0)
                sub.chords.push_back(tmp_chord);
            while (i < chords.size() && t < r * time_signature / 4) {
                if (t + chords[i].duration > r * time_signature / 4) {
                    Chord tmp_chord_again(chords[i]);
                    tmp_chord_again.duration = r * time_signature / 4 - t;
                    sub.chords.push_back(tmp_chord_again);
                    break;
                }
                sub.chords.push_back(Chord(chords[i]));
                t = t + chords[i].duration;
                ++i;
            }
          }
          return sub;
      }
      // if this section is a bridge (means empty)
      bool is_bridge(int tip = 4) const {
          int t = 0;
          int mel_len = melody.size();
          int time_len = ((end - start) * time_signature);
          for (int i = 0; i < mel_len && t < time_len - tip; ++i) {
              if (melody[i].pitch > -2 && t + melody[i].duration > tip && t < time_len - tip)
                  return false;
              t += melody[i].duration;
          }
          return true;
      }
    
      bool is_subsec_bridge(int l, int r, int tip = 4) const {
          Section tmp_sec = this->subsection(l, r);
          if (tmp_sec.is_bridge()) return true;
          if (l > start) {
              Section tmp_sec = this->subsection(l - 1, r);
              int t = 0, i = 0;
              while(i < tmp_sec.melody.size()) {
                  if (tmp_sec.melody[i].pitch > -2 && t < time_signature - 2 && t + tmp_sec.melody[i].duration > time_signature) {
                      int note_length = tmp_sec.melody[i++].duration;
                      while (i < tmp_sec.melody.size() && tmp_sec.melody[i].pitch == -2) note_length += tmp_sec.melody[i++].duration;
                      if (t + note_length >= time_signature * (r - l + 1) - tip) return true;
                      else return false;
                  }
                  t += tmp_sec.melody[i++].duration;
              }
          }
          return false;
      }
    
      bool contains_bridge(int default_rest = 40) {
          int mel_len = melody.size(), t = 0, d, time_len = ((end - start) * time_signature);
          for (int i = 0; i < mel_len && t < time_len; ++i) {
              if (t + melody[i].duration > time_len) d = time_len - t;
              else d = melody[i].duration;
              if (melody[i].pitch == -2 && d >= default_rest) return true;
              t += d;
          }
          return false;
      }
      void printSection() const {
          printf("section (%d, %d): \n", start, end);
          printf("melody ");
          for (int i = 0; i < melody.size(); ++i)
              melody[i].printNote();
          printf("\n");
          for (int i = 0; i < chords.size(); ++i)
              chords[i].printChord();
      }
};

// Match class is a set of sections that considered repetition to each other
// contains an average matching score
class Match {
  public:
      vector<Section> sections;
      double score;
    
      Match() {}

      Match(const Match& x) {
          sections = x.sections;
          score = x.score;
      }

      void insert_section (Section sec) {
          for (vector<Section>::iterator idx = sections.begin(); idx < sections.end(); ++idx)
              if (idx->start > sec.start) {
                  sections.insert(idx, sec);
                  return;
              }
          sections.push_back(sec);
      }
    
    bool is_same(const Match& x) {
        if (sections.size() != x.sections.size()) return false;
        for (int i = 0; i < sections.size(); ++i)
            if (!sections[i].is_same(x.sections[i])) return false;
        return true;
    }

      void printMatch() const {
          for (int i = 0; i < sections.size(); ++i)
              printf( " (%2d, %2d) ", sections[i].start, sections[i].end);
          printf(" : %.6lf \n", score);
      }
};


int bitcount_table[256] = {
        0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 3, 2, 3, 3, 4,
        1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4, 3, 4, 4, 5,
        1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4, 3, 4, 4, 5,
        2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
        1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4, 3, 4, 4, 5,
        2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
        2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
        3, 4, 4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7,
        1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4, 3, 4, 4, 5,
        2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
        2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
        3, 4, 4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7,
        2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6,
        3, 4, 4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7,
        3, 4, 4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7,
        4, 5, 5, 6, 5, 6, 6, 7, 5, 6, 6, 7, 6, 7, 7, 8,
    };

int clear_outtro(const Section &song);
int clear_intro(const Section &song);
    
// Covermap class is used in searching for the best match cover.
// using bitmap to represent the cover status
class Covermap {
  public:
    unsigned long long map[3]; // cover status, bitmap map[0] 0 - 63, map[1] 64 - 127, map[2] 128 - 191
    int length;
    double cost; // current SDL
    double match_score; //current composed rhythm similarity, contour similarity, chord similarity
    Covermap *from; // previous step cover status
    Match cover; // latest match added
    Section *original_song;
    string string_result; // cover results in string representation
    string string_result_merge_extra; // cover result after merging extra 'X' measures
    
      Covermap(int length_, double g, double h, Section* a) {
          length = length_;
          map[0] = map[1] = map[2] = 0;
          cost = h + double(length) * g;
          match_score = 0.0;
          from = NULL;
          original_song = a;
          string_result = "X" + to_string(length);
          string_result_merge_extra = "";
      }

      Covermap(const Covermap& x) {
          length = x.length;
          cost = x.cost;
          from = x.from;
          cover= x.cover;
          match_score = x.match_score;
          map[0] = x.map[0];
          map[1] = x.map[1];
          map[2] = x.map[2];
          string_result = x.string_result;
          string_result_merge_extra = x.string_result_merge_extra;
          original_song = x.original_song;
      }

      bool is_same(Covermap x) {
          if (length != x.length) return 0;
          if (map[0] == x.map[0] && map[1] == x.map[1] && map[2] == x.map[2]) return 1;
          return 0;
      }

      bool is_ok2add_cover(Match x) {
          unsigned long long a = 1, mask, t = - 1;
          int section_len = x.sections.size();
          for (int idx = 0; idx < section_len; ++idx) {
              int s = x.sections[idx].start, e = x.sections[idx].end;
              if (s < 64) {
                  if (e < 64)
                      mask = ((a << (e)) - 1) - ((a << (s)) - 1);
                  else
                      mask = t - ((a << (s)) - 1);
              }
              else mask = 0;
              if ((map[0] & mask) > 0) return 0;
              if (s < 64) s = 64;
              if (s < 128 && e > 64) {
                  if (e < 128)
                      mask = ((a << (e - 64)) - 1) - ((a << (s - 64)) - 1);
                  else
                      mask = t - ((a << (s - 64)) - 1);
              }
              else mask = 0;
              if ((map[1] & mask) > 0) return 0;
              if (s < 128) s = 128;
              if (e > 128) {
                  mask = ((a << (e - 128)) - 1) - ((a << (s - 128)) - 1);
              }
              else mask = 0;
              if ((map[2] & mask) > 0) return 0;
          }
          return 1;
      }
    
      int bitonecount(const unsigned long long n) {
        return bitcount_table[n & 0xff] +
            bitcount_table[(n >>8) & 0xff] +
            bitcount_table[(n >>16) & 0xff] +
            bitcount_table[(n >>24) & 0xff] +
            bitcount_table[(n >>32) & 0xff] +
            bitcount_table[(n >>40) & 0xff] +
            bitcount_table[(n >>48) & 0xff] +
            bitcount_table[(n >>56) & 0xff];
      }
    
      int getmap_at(int position) {
          if (position < 64) return int((map[0] >> position) & 1);
          if (position < 128) return int((map[1] >> (position - 64)) & 1);
          return int((map[2] >> (position - 128)) & 1);
      }
    
      double best_possible_cost(double g, double h, int begin, int real_end) {
          unsigned long long a = 1;
          int l = 0;
          if (begin < 64) l = bitonecount(map[0]) + bitonecount(map[1]) + bitonecount(map[2]) - bitonecount(map[0] & ((a << begin) - 1));
          else if (begin < 128) l = bitonecount(map[1]) + bitonecount(map[2]) - bitonecount(map[1] & ((a << (begin - 64)) - 1));
          else l = bitonecount(map[2]) - bitonecount(map[2] & ((a << (begin - 128)) - 1));
          
          l = real_end - begin - l;
          if (l < 8) return cost;
          return cost - g * double(l - 4) - h * (1.0 - double(l /4));
      }

      void printMap () const {
          printf("Covermap: Length %d, c %.2lf, m %.2lf [ ", length, cost, match_score);
          for (int i = 0; i < length; ++i) {
              if (i < 64) printf("%d ", int((map[0] >> i) & 1));
              else if (i < 128) printf("%d ", int((map[1] >> (i - 64)) & 1));
              else printf("%d ", int((map[2] >> (i - 128)) & 1));
          }
          printf("], last cover ");
          for (int i = 0; i < cover.sections.size(); ++i)
              printf(" (%d, %d) ", cover.sections[i].start, cover.sections[i].end);
          if (from != NULL)
              printf(" from %.2lf\n", from->cost);
          printf("\n");
      }
    
      void toString() {
          int real_end = clear_outtro(*original_song);
          int real_start = clear_intro(*original_song);
          if (real_end > length) real_end = length;
          
          if (map[0] == 0 && map[1] == 0 && map[2] == 0) {
              string_result = "";
              if (real_start > 0) string_result += "i" + to_string(real_start);
              string_result += "X" + to_string(real_end - real_start);
              if (real_end < length) string_result += "o" + to_string(length - real_end);
              return;
          }
          Covermap* i = this;
          vector<Match> used;
          vector<double> costs;
          while (1) {
              if (i->cover.sections.size() > 0) {
                  used.push_back(i->cover);
                  costs.push_back(i->cost);
              }
            if (i->from == NULL) break;
            i = i->from;
         }
          
        Match ordered;
        int result_map[length];
        memset(result_map, 'X', sizeof(result_map));

        for (int j = 0; j < used.size(); ++j) {
            for (int k = 0; k < used[j].sections.size(); ++k) {
                ordered.insert_section(used[j].sections[k]);
                for (int r = used[j].sections[k].start; r < used[j].sections[k].end; ++r)
                    result_map[r] = j;
            }
        }

        int t = 0;
        string result = "";
        char f[used.size()];
        memset(f, 0, sizeof(f));
        char flag = 'A';
        char bridge_flag = 'b';
        
        if (real_start > 0) {
            result += "i" + to_string(real_start);
            t = real_start;
        }
        for (int j = 0; j < ordered.sections.size(); ++j) {
            if (ordered.sections[j].start > t) {
                Section tmp_sub = original_song->subsection(t, ordered.sections[j].start);
                if (tmp_sub.is_bridge() || original_song->is_subsec_bridge(t, ordered.sections[j].start)) {
                    result += 'x';
                    result += to_string(ordered.sections[j].start - t);
                } else if (tmp_sub.contains_bridge()) {
                    int tmp_measure_count = 0, kr;
                    for (kr = 0; kr < tmp_sub.melody.size(); ++kr) {
                        if (tmp_sub.melody[kr].duration >= 40 && tmp_sub.melody[kr].pitch == -2)
                            break;
                        tmp_measure_count += tmp_sub.melody[kr].duration;
                    }
                    int bridge_start = tmp_measure_count / (original_song->time_signature) + int((tmp_measure_count % (original_song->time_signature)) > 4);
                    int bridge_end = (tmp_measure_count + tmp_sub.melody[kr].duration) / (original_song->time_signature)  + int(((tmp_measure_count + tmp_sub.melody[kr].duration) % (original_song->time_signature)) > ((original_song->time_signature / 2)));
                    if (bridge_start > 0) {
                        result += 'X';
                        result += to_string(bridge_start);
                    }
                    if (t + bridge_end > ordered.sections[j].start)
                        bridge_end = ordered.sections[j].start - t;
                    result += 'x';
                    
                    int left_over = (ordered.sections[j].start - t) * (original_song->time_signature) -
                                    (tmp_measure_count + tmp_sub.melody[kr].duration);
                    
                    if (t + bridge_end + 1 == ordered.sections[j].start && left_over <= (original_song->time_signature / 2))
                        result += to_string(bridge_end - bridge_start + 1);
                    else {
                        result += to_string(bridge_end - bridge_start);
                        if (t + bridge_end < ordered.sections[j].start) {
                            result += 'X';
                            result += to_string(ordered.sections[j].start - t - bridge_end);
                        }
                    }
                } else {
                    if (tmp_sub.melody[0].duration >= (original_song->time_signature) && tmp_sub.melody[0].pitch == -2) {
                        result += 'x';
                        result += to_string(tmp_sub.melody[0].duration / (original_song->time_signature) +
                                            int((tmp_sub.melody[0].duration % (original_song->time_signature)) >= (original_song->time_signature / 2)));
                        t += tmp_sub.melody[0].duration / (original_song->time_signature) +
                        int((tmp_sub.melody[0].duration % (original_song->time_signature)) >= (original_song->time_signature / 2));
                    }
                    if (t < ordered.sections[j].start) {
                        result += 'X';
                        result += to_string(ordered.sections[j].start - t);
                    }
                }
            }
            if (f[result_map[ordered.sections[j].start]] == 0) {
                if (ordered.sections[j].is_bridge())
                    f[result_map[ordered.sections[j].start]] = bridge_flag++;
                else
                    f[result_map[ordered.sections[j].start]] = flag++;
            }
            result += f[result_map[ordered.sections[j].start]];
            result += to_string(ordered.sections[j].end - ordered.sections[j].start);
            t = ordered.sections[j].end;
        }
        if (t < real_end) {
              result += 'X';
              result += to_string(real_end - t);
              t = real_end;
        }
        if (t < length) {
            result += 'o';
            result += to_string(length - t);
        }
        string_result = result;
      }
    
    int longest_note(vector<Note> melody, int tip = 16) {
        int longest = 1;
        int i = melody.size() - 1;
        int pos = 0;
        while (i >= 0 && pos <= tip) {
            if (melody[i].pitch == -2 && i > 0) {
                pos += melody[i].duration;
                i--;
                int tmp = melody[i].duration + melody[i + 1].duration;
                if (tmp > longest) longest = tmp;
            }
            else if (melody[i].duration > longest) longest = melody[i].duration;
            pos += melody[i--].duration;
        }
        return longest;
    }
    
    bool contain_match(const pair<Section, Section> candidate, const vector<pair<Section, Section> > &matches) {
        for (int i = int(matches.size()) - 1; i >= 0; --i) {
            if (candidate.first.start == matches[i].first.start &&
                candidate.first.end == matches[i].first.end &&
                candidate.second.start == matches[i].second.start &&
                candidate.second.end == matches[i].second.end)
                return true;
        }
        return false;
    }
    
    void small_extra_merge() {
        if (string_result_merge_extra == "") string_result_merge_extra = string_result;
        if (string_result_merge_extra == "") return;
        int i = 0;
        vector<pair<char, int> > phrases;
        phrases.clear();
        while (i < string_result_merge_extra.length()) {
            char label = string_result_merge_extra[i++];
            int num = 0;
            while (i < string_result_merge_extra.length() &&
                   string_result_merge_extra[i] >= '0' && string_result_merge_extra[i] <= '9')
                num = num * 10 + string_result_merge_extra[i++] - '0';
            phrases.push_back(make_pair(label, num));
        }
        
        for (int times = 0; times <= 1; ++times) {
            for (i = phrases.size() - 2; i >= 0; --i) {
                if (phrases[i].first >= 'A' && phrases[i].first <= 'Z' && phrases[i].first != 'X' &&
                    (phrases[i + 1].first == 'x'  || phrases[i + 1].first == 'X') && phrases[i + 1].second == 1) {
                    bool flag1 = (i + 2 == phrases.size() || (phrases[i + 2].first >= 'A' && phrases[i + 2].first <= 'Z'));
                    bool flag2 = ((phrases[i].second + phrases[i + 1].second) % 4 == 0 || phrases[i + 1].first == 'x');
                    if (flag1 && flag2){
                        phrases[i].second += phrases[i + 1].second;
                        phrases.erase(phrases.begin() + i + 1);
                    }
                    else {
                        bool delete_flag = false;
                        for (int j = 0; j < phrases.size() && !delete_flag; ++j)
                            if (phrases[i].first == phrases[j].first && phrases[i].second + 1 == phrases[j].second) {
                                phrases[i].second += phrases[i + 1].second;
                                phrases.erase(phrases.begin() + i + 1);
                                delete_flag = true;
                            }
                    }
                }
            }
        }
        
        string new_merge_result = "";
        for (i = 0; i < phrases.size(); ++i)
           new_merge_result += phrases[i].first + to_string(phrases[i].second);
        string_result_merge_extra = new_merge_result;
    }
    
    void merge_extra(const vector<pair<Section, Section> > &matches, bool small_extra_only = false) {
        if (string_result == "") return;
        int i = 0;
        int current_pos = 0;
        char prev_label = 'i';
        vector<pair<char, int> > new_result;
        vector<int> new_pos_end;
        vector<pair<int, Section> > long_extra;
        char max_label = 'A';
        
        while (i < string_result.length()) {
            char label = string_result[i++];
            if (label >= 'A' && label <= 'Z' && label != 'X' && label > max_label) max_label = label;
            int num = 0;
            while (i < string_result.length() && string_result[i] >= '0' && string_result[i] <= '9')
                num = num * 10 + string_result[i++] - '0';
            
            current_pos += num;
            
            if ((prev_label >= 'A' && prev_label <= 'Z' && (!small_extra_only || (small_extra_only && num <= 2))) &&
                (label == 'X' || (label == 'x' && !original_song->subsection(current_pos - num, current_pos).is_bridge()))) {
                int lowerbound_longest_note = -1;
                int prev_num = new_result.back().second;
                for (int j = 0; j < new_result.size() - 1; ++j)
                    if (new_result[j].first == prev_label) {
                        Section tmp = (original_song->subsection(new_pos_end[j] - 1, new_pos_end[j]));
                        int tmp_ln = longest_note(tmp.melody, original_song->time_signature);
                        if (lowerbound_longest_note == -1 || tmp_ln < lowerbound_longest_note) lowerbound_longest_note = tmp_ln;
                    }
                if (lowerbound_longest_note >= 8 || lowerbound_longest_note == -1) lowerbound_longest_note = 8;
                int extra_lowerbound_longest_note = lowerbound_longest_note;
                if (extra_lowerbound_longest_note < 6) extra_lowerbound_longest_note = 6;
                bool flag0 = false, flag1 = false, flag2 = false;
                Section m0 = (original_song->subsection(current_pos - num - 1, current_pos - num));
                Section m1 = (original_song->subsection(current_pos - num, current_pos - num + 1));
                //Section m2 = (original_song->subsection(current_pos - num + 1, current_pos - num + 2));//
                int ln0 = longest_note(m0.melody, original_song->time_signature);
                int ln1 = longest_note(m1.melody, original_song->time_signature), ln2 = 0;
                if (extra_lowerbound_longest_note < 8 && extra_lowerbound_longest_note < ln0 + 2)
                    extra_lowerbound_longest_note = ln0 + 2;
                if (num > 1) {
                    Section m2 = (original_song->subsection(current_pos - num + 1, current_pos - num + 2));
                    ln2 = longest_note(m2.melody, original_song->time_signature);
                    if (ln2 >= extra_lowerbound_longest_note) flag2 = true;
                    if (m2.is_bridge(0)) flag2 = false;
                }
                if (ln0 >= lowerbound_longest_note) flag0 = true;
                if (ln1 >= extra_lowerbound_longest_note) flag1 = true;
                if (m1.is_bridge(0)) flag1 = flag2 = false;
                if (m0.is_bridge(0)) flag1 = flag2 = false;
                if (ln0 >= 8 && prev_num % 4 == 0 &&
                    (num > 2 || (i < string_result.length() && string_result[i] >= 'A' && string_result[i] <= 'Z')))
                    {flag0 = true; flag1 = flag2 = false;}
                if (label == 'x' && ln0 >= 4 && prev_num % 4 == 0)  {flag0 = true; flag1 = flag2 = false;}
                
                
                int decision = 0;
                if (flag2) {
                    if (flag0 && flag1) {
                        if (ln2 >= ln1 && ln2 >= ln0) decision = 2;
                        else if (ln1 >= ln0 && ln1 >= ln2) decision = 1;
                    }
                    else if (flag0 || flag1) {
                        if (flag1) {
                            if (ln2 >= ln1) decision = 2;
                            else decision = 1;
                        }
                        else {
                            if (ln2 >= ln0) decision = 2;
                        }
                    }
                    else decision = 2;
                }
                else if (flag1) {
                    if (flag0) {
                        if (ln1 >= ln0) decision = 1;
                    }
                    else decision = 1;
                }
                else if (!flag0 && !flag1 && !flag2) {
                    if (ln2 >= ln1 && ln2 >= ln0) decision = 2;
                    else if (ln1 >= ln2 && ln1 >= ln0) decision = 1;
                }
                
                num -= decision;
                new_result[new_result.size() - 1].second += decision;
                new_pos_end[new_result.size() - 1] += decision;
            }
            
            if (num > 0) {
                new_result.push_back(make_pair(label, num));
                new_pos_end.push_back(current_pos);
                if (num >= 4 && label == 'X')
                    long_extra.push_back(
                            make_pair(new_result.size() - 1, original_song->subsection(current_pos - num, current_pos)));
            }
            prev_label = label;
        }
        
        for (int i = 0; i < long_extra.size(); ++i) {
            int j;
            for (j = i + 1; j < long_extra.size(); ++j) {
                if (new_result[long_extra[i].first].second == new_result[long_extra[j].first].second &&
                    contain_match(make_pair(long_extra[i].second, long_extra[j].second), matches)) {
                    new_result[long_extra[i].first].first = max_label + 1;
                    new_result[long_extra[j].first].first = max_label + 1;
                    max_label++;
                    break;
                }
            }
            if (j < long_extra.size()) break;
        }
        
        
        char current_label = 'A' - 1;
        for (int i = 0; i < new_result.size(); ++i) {
            if (new_result[i].first >= 'A' && new_result[i].first <= 'Z' && new_result[i].first != 'X'
                && current_label < new_result[i].first) {
                if (current_label + 1 == new_result[i].first) current_label++;
                else {
                    //switch label
                    char label1 = current_label + 1;
                    char label2 = new_result[i].first;
                    vector<int> candidate1;
                    vector<int> candidate2;
                    for (int j = i; j < new_result.size(); ++j) {
                        if (new_result[j].first == label1) candidate1.push_back(j);
                        else if (new_result[j].first == label2) candidate2.push_back(j);
                    }
                    for (int j = 0; j < candidate1.size(); ++j)
                        new_result[candidate1[j]].first = label2;
                    for (int j = 0; j < candidate2.size(); ++j)
                        new_result[candidate2[j]].first = label1;
                    current_label++;
                }
            }
        }
        
        vector<int> start_pos;
        start_pos.push_back(0);
        for (i = 1; i < new_result.size(); ++i)
            start_pos.push_back(start_pos[i - 1] + new_result[i - 1].second);
        
        i = 0;
        while (i < new_result.size()) {
            if (i + 1 < new_result.size() &&
                new_result[i].first >= 'A' && new_result[i].first <= 'Z' && new_result[i].first != 'X' &&
                new_result[i].second >= 6 && new_result[i].second < 8 && new_result[i + 1].first == 'X' &&
                new_result[i + 1].second + new_result[i].second == 8) {
                vector<int> candidates;
                candidates.clear();
                candidates.push_back(i);
                bool valid_flag = true;
                for (int j = i + 2; j + 1 < new_result.size(); ++j) {
                    if (new_result[j].first == new_result[i].first &&
                        new_result[j + 1].first == 'X' && new_result[j + 1].second + new_result[j].second == 8 &&
                        contain_match(make_pair(original_song->subsection(start_pos[i], start_pos[i] + 8),
                                                original_song->subsection(start_pos[j], start_pos[j] + 8)), matches)) {
                        candidates.push_back(j);
                    }
                    else if (new_result[j].first == new_result[i].first && new_result[j].second <= 5)
                        valid_flag = false;
                }
                for (int j = 0; j < i && valid_flag; ++j) {
                    if (new_result[j].first == new_result[i].first && new_result[j].second <= 5 &&
                        new_result[j + 1].first != 'X')
                        valid_flag = false;
                }
                if (candidates.size() > 1 && valid_flag) {
                    for (int j = candidates.size() - 1; j >= 0; --j) {
                        int t = candidates[j];
                        new_result[t].second += new_result[t + 1].second;
                        new_result.erase(new_result.begin() + t + 1);
                        start_pos.erase(start_pos.begin() + t + 1);
                    }
                }
            }
            ++i;
        }
        
        string_result_merge_extra = "";
        start_pos.clear();
        start_pos.push_back(0);
        for (i = 1; i < new_result.size(); ++i)
            start_pos.push_back(start_pos[i - 1] + new_result[i - 1].second);
        for (i = 0; i < new_result.size(); ++i) {
            if (new_result[i].first == 'X' &&
                (original_song->subsection(start_pos[i], start_pos[i] + new_result[i].second)).is_bridge()) {
                new_result[i].first = 'x';
                if (i + 1 < new_result.size() && new_result[i + 1].first == 'x') {
                    new_result[i].second += new_result[i + 1].second;
                    new_result[i + 1].second = 0;
                }
                else if (i + 1 < new_result.size() && new_result[i + 1].first == 'o') {
                    new_result[i + 1].second += new_result[i].second;
                    new_result[i].second = 0;
                }
            }
            if (new_result[i].second > 0)
                string_result_merge_extra += new_result[i].first + to_string(new_result[i].second);
        }
    }
    
    double calculate_cost(double g, double h, const string &result) {
        if (result == "") return (original_song->end - original_song->start) * g + h;
        int i = 0;
        vector<pair<char, int> > phrases;
        phrases.clear();
        while (i < result.length()) {
            char label = result[i++];
            int num = 0;
            while (i < result.length() && result[i] >= '0' && result[i] <= '9')
                num = num * 10 + result[i++] - '0';
            phrases.push_back(make_pair(label, num));
        }
        
        for (int times = 0; times <= 1; ++times) {
            for (i = phrases.size() - 2; i >= 0; --i) {
                if (phrases[i].first >= 'A' && phrases[i].first <= 'Z' && phrases[i].first != 'X' &&
                    phrases[i + 1].first == 'x' && phrases[i + 1].second <= 1) {
                    if (i + 2 == phrases.size() || (phrases[i + 2].first >= 'A' && phrases[i + 2].first <= 'Z')) {
                        phrases[i].second += phrases[i + 1].second;
                        phrases.erase(phrases.begin() + i + 1);
                    }
                    else {
                        bool delete_flag = false;
                        for (int j = 0; j < phrases.size() && !delete_flag; ++j)
                            if (phrases[i].first == phrases[j].first && phrases[i].second + 1 == phrases[j].second) {
                                phrases[i].second += phrases[i + 1].second;
                                phrases.erase(phrases.begin() + i + 1);
                                delete_flag = true;
                            }
                    }
                }
            }
        }
        
        for (i = phrases.size() - 2; i >= 0; --i) {
            if (phrases[i].first >= 'A' && phrases[i].first <= 'Z' && phrases[i].first != 'X' &&
                phrases[i + 1].first == 'x' && phrases[i + 1].second <= 1 &&
                (i + 2 == phrases.size() || (phrases[i + 2].first >= 'A' && phrases[i + 2].first <= 'Z'))){
                    phrases[i].second += phrases[i + 1].second;
                    phrases.erase(phrases.begin() + i + 1);
                }
        }
        
        double new_cost = -2.0;
        int counts[54], sum[54];
        memset(counts, 0, sizeof(counts));
        memset(sum, 0, sizeof(sum));
        for (i = 0; i < phrases.size(); i++) {
            if (phrases[i].first >= 'A' && phrases[i].first <= 'Z' && phrases[i].first != 'X') {
                counts[phrases[i].first - 'A']++;
                sum[phrases[i].first - 'A'] += phrases[i].second;
            }
            else if (phrases[i].first >= 'a' && phrases[i].first <= 'z' && phrases[i].first != 'x'){
                counts[phrases[i].first - 'a' + 26]++;
                sum[phrases[i].first - 'a' + 26] += phrases[i].second;
            }
            else if (phrases[i].first == 'x' || phrases[i].first == 'X'){
                new_cost += g * phrases[i].second;
                if (i == 0 || (phrases[i - 1].first != 'x' && phrases[i - 1].first != 'X')) new_cost += h;
                else if (phrases[i].first != phrases[i - 1].first &&
                         phrases[i].second >= 2 && phrases[i - 1].second >= 2 &&
                         phrases[i].second + phrases[i - 1].second > 4) new_cost += h;
            }
        }
        
        for (i = 0; i < 54; ++i)
            if (counts[i] > 0)
                new_cost += h * double(counts[i]) + g * double(sum[i]) / double(counts[i]);
        return new_cost;
    }
    
    int calculate_cover_area(string result) {
        if (result == "") return 0;
        int area = 0;
        int i = 0;
        int current_pos = 0;
        while (i < result.size()) {
            char label = result[i++];
            int num = 0;
            while (i < result.length()
                   && result[i] >= '0' && result[i] <= '9')
                num = num * 10 + result[i++] - '0';
            if (label >= 'A' && label <='Z' && label != 'X') area += num;
            else if (label >= 'a' && label <= 'z') area += num;
            current_pos += num;
        }
        return area;
    }
    
    bool boundary_checking(string result) {
        if (result == "") return false;
        int i = 0;
        char prev_label = 'i';
        int prev_num = 16;
        int current_pos = 0;
        while (i < result.size()) {
            char label = result[i++];
            int num = 0;
            while (i < result.length()
                   && result[i] >= '0' && result[i] <= '9')
                num = num * 10 + result[i++] - '0';
            if (label >= 'A' && label <='Z' && label != 'X'
                && prev_label >= 'A' && prev_label <='Z' && prev_label != 'X'
                && prev_num % 4 != 0 && prev_label != label) {
                Section m0 = original_song->subsection(current_pos - 2, current_pos - 1);
                Section m1 = original_song->subsection(current_pos - 1, current_pos);
                Section m2 = original_song->subsection(current_pos, current_pos + 1);
                int ln0 = longest_note(m0.melody, original_song->time_signature);
                int ln1 = longest_note(m1.melody, original_song->time_signature);
                int ln2 = longest_note(m2.melody, original_song->time_signature);
                if ((ln1 <= (original_song->time_signature) / 2 - 2 && ln2 >= (original_song->time_signature - 4)) ||
                    (ln1 <= 4 && ln2 - ln1 >= 4)) return false;
                if ((ln1 <= (original_song->time_signature) / 2 - 2 && ln0 >= (original_song->time_signature - 4)) ||
                    (ln1 <= 4 && ln0 - ln1 >= 4) || (ln1 <= 8 && ln0 >= 14)) return false;
            }
            prev_label = label;
            prev_num = num;
            current_pos += num;
        }
        return true;
    }
    
    // extra control in addition to SDL
    double length_variance(string result) {
        if (result == "") return 100000.0;
        int i = 0;
        vector<pair<char, int> > phrases;
        char max_label = ' ';
        int total_length = 0;
        while (i < result.size()) {
            char label = result[i++];
            int num = 0;
            while (i < result.length() && result[i] >= '0' && result[i] <= '9')
                num = num * 10 + result[i++] - '0';
            phrases.push_back(make_pair(label, num));
            if (label != 'o' && label != 'i') total_length += num;
            if (label >= 'A' && label <= 'Z' && label != 'X' && label > max_label) max_label = label;
        }
        if (max_label < 'A') return 0.0;
        
        for (i = phrases.size() - 2; i >= 0; --i) {
            if (phrases[i].first >= 'A' && phrases[i].first <= 'Z' && phrases[i].first != 'X' &&
                phrases[i + 1].first == 'x' && phrases[i + 1].second <= 1 &&
                (phrases[i].second + phrases[i + 1].second) % 4 == 0){
                    phrases[i].second += phrases[i + 1].second;
                    phrases.erase(phrases.begin() + i + 1);
                }
        }
        
        
        double ans = 0.0;
        for (char label = 'A'; label <= max_label; ++label) {
            double avg_len = 0.0;
            double num = 0.0;
            for (i = 0; i < phrases.size(); ++i)
                if (phrases[i].first == label) {avg_len += double(phrases[i].second); num += 1.0;}
            avg_len /= num;
            int std = 4;
            if (avg_len > 14.0) std = 16;
            else if (avg_len > 11.0) std = 12;
            else if (avg_len > 6.0) std = 8;
            
            bool std_appear = false;
            for (i = 0; i < phrases.size(); ++i)
                if (phrases[i].first == label && phrases[i].second == std && i + 1 < phrases.size() && phrases[i + 1].first != 'o')
                    std_appear = true;
            
            for (i = 0; i < phrases.size(); ++i)
                if (phrases[i].first == label && phrases[i].second != std) {
                    if (phrases[i].second < std) {
                        if (std_appear)
                            ans += 32.0 / double(std);
                        else
                            ans += 2.0;
                    }
                    else {
                        double tip = double(phrases[i].second - std) / 2.0;
                        if (phrases[i].second == std + 1 && std != 12) tip = 0;
                        if (phrases[i].second == std + 2 && std > 4) tip = 0.5;
                        if (phrases[i].second == std + 2 && std == 4 &&
                            (i + 1 == phrases.size() || (phrases[i + 1].first >= 'a' && phrases[i + 1].first <= 'z')))
                            tip /= 2.0;
                        ans += tip * tip;
                    }
                }
        }
        
        // secessive variance
        for (i = 0; i < phrases.size(); ++i) {
            if (i + 1 < phrases.size() &&
                phrases[i].first >= 'A' && phrases[i].first <= 'Z' && phrases[i].first != 'X' &&
                phrases[i + 1].first >= 'A' && phrases[i + 1].first <= 'Z' && phrases[i + 1].first != 'X' &&
                abs(phrases[i].second - phrases[i + 1].second) >= 7 && (phrases[i].second <= 6 || phrases[i + 1].second <= 6)) {
                if (phrases[i + 1].second <= 6) {
                    if (i + 2 >= phrases.size() || phrases[i + 2].first != phrases[i + 1].first) ans += 2.0;
                }
                else {
                    if (i == 0 || phrases[i - 1].first != phrases[i].first) ans += 2.0;
                }
                
            }
        }
        double factor = 1.0;
        if (total_length > 60) factor = double(total_length) / 60.0;
        return ans * factor;
    }
    
    bool is_boundary(int k) {
        if (string_result == "") return false;
        int i = 0, t = 0;
        while (i < string_result.size() && t < k) {
            int num = 0;
            i++;
            while (i < string_result.size() && string_result[i] >= '0' && string_result[i] <= '9')
                num = num * 10 + string_result[i++] - '0';
            t += num;
            if (t == k) return true;
            if (t > k) return false;
        }
        return false;
    }
};



/* =====================      Repetition & Similarity Detection       ====================== */

// Similarity distance between two chords
double chord_dist(Chord x, Chord y) {
    // chord tones
    int tp = 0, tn = 0, fp = 0, fn = 0;
    for (int i = 0; i < 12; ++i) {
        if (x.tones[i] && y.tones[i]) tp++;
        if (x.tones[i] && !y.tones[i]) fp++;
        if (!x.tones[i] && y.tones[i]) fn++;
        if (!x.tones[i] && !y.tones[i]) tn++;
    }
    double precision = double(tp) / double(tp + fp);
    double recall = double(tp) / double(tp + fn);
    double f1 = 2.0 * precision * recall / (precision + recall);
    if (precision + recall < 1e-8)
        f1 = 0.0;

    // appear position, e.g. for every x, what is the distance of the nearest y
    // similarity between previous chord and next chord, prev_chord_vector of x vs. y
    return f1;
}

bool is_empty_melody(vector<int> &x, int tip = 4) {
    int len =  x.size();
    for (int i = tip; i < len - tip; ++i)
        if (x[i] > -2)
            return false;
    return true;
}

int melody_ending_possible(vector<int> &x) {
    int longest = 0, temp_len;
    vector<int>::iterator i = x.end() - 1;
    while (i >= x.begin()) {
        if (*i == -2) {
            temp_len = 0;
            while (i >= x.begin() && *i == -2) {
                ++temp_len;
                --i;
            }
            while (i >= x.begin()) {
                --i;
                ++temp_len;
                if (i >= x.begin() && *i != *(i + 1)) break;
            }
            if (temp_len > longest) longest = temp_len;
        }
        else {
            temp_len = 0;
            while (i >= x.begin()) {
                --i;
                ++temp_len;
                if (i >= x.begin() && *i != *(i + 1)) break;
            }
            if (temp_len > longest) longest = temp_len;
        }
    }
    return longest;
}

int get_contour_dist(vector<int> &a, int i, vector<int> &b, int j) {
    int x = 0, y = 0;
    if (a[i] == -2 && b[j] == -2) x = 0;
    else if (a[i] == -2 || b[j] == -2) x = 14;
    else x = abs(a[i] - b[j]);

    if (i > 0 && j > 0 && a[i] >= 0 && b[j] >= 0) {
        int ta = a[i], tb = b[j];
        i = i - 1;
        while (i >= 0 && a[i] == -2)
            i = i - 1;
        j = j - 1;
        while (j >= 0 && b[j] == -2)
            j = j - 1;
        if (i >= 0 && j >= 0) {
            ta = a[i] - ta;
            tb = b[j] - tb;
            if (ta * tb > 0 || ta == tb)
                y = 0;
            else if (ta * tb < 0)
                y = 2;
            else
                y = 1;
        }
    }
    return x + y * 2;
}

int min3(int a, int b, int c) {
    if (a <= b && a <= c) return a;
    if (b <= c && b <= a) return b;
    return c;
}
int max(int a, int b) {
    if (a >= b) return a;
    return b;
}
int min(int a, int b) {
    if (a <= b) return a;
    return b;
}

double insert_contour_cost(int x, int averx) {
    if (x >= 0) return abs(x - averx);
    return 10;
}

int get_average_melody(const vector<int> &x) {
    int lx = int(x.size());
    int average_pitch_x = 0, nonzero = 0;
    for (int i = 0; i < lx; ++i)
        if (x[i] > -2) {average_pitch_x += x[i]; nonzero++;}
    if (nonzero > 0) average_pitch_x = average_pitch_x / nonzero;
    else average_pitch_x = 60;
    return average_pitch_x;
}

// Melody Contour Similarity between two melodies using Dynamic Time Warping (DTW)
double contour_rating(vector<int> &x, vector<int> &y, int window = 2) {
    int lx = int(x.size()), ly = int(y.size());
    int average_pitch_x = get_average_melody(x), average_pitch_y = get_average_melody(y);
    
    int dtw[lx + 1][ly + 1];
    for (int i = 0; i <= lx; ++i)
        for (int j = 0; j <= ly; ++j)
            dtw[i][j] = 1000000;
    
    dtw[0][0] = 0;
    for (int i = 1; i <= lx; ++i)
        for (int j = max(1, i - window); j <= min(ly, i + window); ++j) {
            dtw[i][j] = min3(dtw[i - 1][j - 1] + get_contour_dist(x, i - 1, y, j - 1),
                             dtw[i - 1][j] + insert_contour_cost(x[i - 1], average_pitch_y),
                             dtw[i][j - 1] + insert_contour_cost(y[j - 1], average_pitch_x));
            if (i <= 4 && j <= 4)
                dtw[i][j] = 0;
        }

    int std = 0;
    for (int i = 0; i < lx; ++i) {
        if (x[i] != -2) std += abs(x[i] - average_pitch_x + 2) + 1;
        else std += 12;
    }
    for (int i = 0; i < ly; ++i) {
        if (y[i] != -2) std += abs(y[i] - average_pitch_y + 2) + 1;
        else std += 12;
    }
    std /= 2;
    int ans = dtw[lx][ly];
    if (abs(lx - ly) > window) {
        if (lx > ly)
            ans = dtw[ly + window][ly] + 10 * (lx - ly);
        else
            ans = dtw[lx][lx + window] + 10 * (ly - lx);
    }
    if (ans >= std) return 0.0;
    return 1.0 - double(ans) / double(std);
}

// Rhythm onsets similarity between two melodies
double rhythm_rating(const vector<Note> &x, const vector<Note> &y) {
    //b   0      0      -1      -1
    //a   0     -1       0      -1
    //  tp+1   fn+1    fp+1   tn+1
    int tp = 0, fp = 0, fn = 0, tn = 0;
    int lx = int(x.size()), ly = int(y.size());
    int t1 = 0, t2 = 0;
    int i = 0, j = 0, a, b;
    for (int t = 0; i < lx && j < ly; ++t) {
        if (t1 + x[i].duration <= t) {
            t1 += x[i].duration;
            ++i;
            b = 0;
        } else b = -1;
        if (x[i].pitch == -2) b = -1;
        if (t2 + y[j].duration <= t) {
            t2 += y[j].duration;
            ++j;
            a = 0;
        } else a = -1;
        if (y[j].pitch == -2) a = -1;
        
        if (a == b) {
            if (a == 0) tp++;
            else tn++;
        } else if (a == 0) fp++;
        else fn++;
    }
    double precision = 1.0, recall = 1.0, acc = 1.0, f1 = 1.0;
    if (tp + fp > 0)
        precision = double(tp) / double(tp + fp);
    if (tp + fn > 0)
        recall = double(tp) / double(tp + fn);
    if (tp + tn + fp + fn > 0)
        acc = double(tp + tn) / double(tp + tn + fp + fn);
    if (tp + fp + fn > 0)
        f1 = 2.0 * double(tp) / double(tp + tp + fp + fn);
    
    return acc;
}

pair<double, double> get_begin_melody_score(const vector<int> &x, const vector<int> &y, int time_signature) {
    int length_x = x.size() / time_signature;
    
    vector<int> sx(x.begin(), x.begin() + time_signature);
    vector<int> sy(y.begin(), y.begin() + time_signature);
    vector<int> nrx = x;
    vector<int> nry = y;
    for (int i = 0; i < x.size(); ++i)
        if (i > 0 && nrx[i] == -2) nrx[i] = nrx[i - 1];
    for (int i = 0; i < y.size(); ++i)
        if (i > 0 && nry[i] == -2) nry[i] = nry[i - 1];
    
    vector<int> nrsx(nrx.begin(), nrx.begin() + time_signature);
    vector<int> nrsy(nry.begin(), nry.begin() + time_signature);
    double cr_score0 = contour_rating(nrsx, nrsy);
    
    int t = 4 * time_signature;
    if (length_x == 4) t = 2 * time_signature;
    vector<int> nrbx(nrx.begin(), nrx.begin() + t);
    vector<int> nrby(nry.begin(), nry.begin() + t);
    double cr_score1 = contour_rating(nrbx, nrby);
    return make_pair(cr_score0, cr_score1);
}

// melody pitch similarity mainly using results from pitch contour similarity
double melody_dist(vector<int> &x, vector<int> &y, int time_signature,
                   bool waive_ending = false) {
    int length_x = x.size() / time_signature;
    
    bool ty = is_empty_melody(y), tx = is_empty_melody(x);
    if (tx != ty) return 0.0;
    if (tx && ty) return 1.0;
    
    
    vector<int> nx(x.end() - time_signature, x.end());
    vector<int> ny(y.end() - time_signature, y.end());
    vector<int> nnx(x.end() - time_signature * 2, x.end());
    vector<int> nny(y.end() - time_signature * 2, y.end());
    if (is_empty_melody(nnx, 0) && is_empty_melody(nny, 0)) return 0.0;
    if (is_empty_melody(nx, 0) && is_empty_melody(ny, 0)) return 0.0;
    tx = is_empty_melody(nnx, 2);
    ty = is_empty_melody(nny, 2);
    if (tx != ty) {
        if (tx && melody_ending_possible(nny) < time_signature * 2 - 4) return 0.0;
        if (ty && melody_ending_possible(nnx) < time_signature * 2 - 4) return 0.0;
    }
    tx = is_empty_melody(nx, 2);
    ty = is_empty_melody(ny, 2);
    if (tx != ty) {
        if (tx && melody_ending_possible(ny) < time_signature - 6) return 0.0;
        if (ty && melody_ending_possible(nx) < time_signature - 6) return 0.0;
        if (tx && melody_ending_possible(nny) >= 16) return 0.0;
        if (ty && melody_ending_possible(nnx) >= 16) return 0.0;
    }
    
    vector<int> sx(x.begin(), x.begin() + time_signature);
    vector<int> sy(y.begin(), y.begin() + time_signature);
    tx = is_empty_melody(sx, 2);
    ty = is_empty_melody(sy, 2);
    if (tx || ty) return 0.0;
    tx = is_empty_melody(sx, 0);
    ty = is_empty_melody(sy, 0);
    if (tx && ty) return 0.0;
    
    double score = 1.0;
    if (!waive_ending) {
        int ttx = melody_ending_possible(nx);
        int tty = melody_ending_possible(ny);
    
        if (abs(ttx - tty) >= 4 && (ttx < 4 || tty < 4)) score *= 0.7;
        if (ttx < 4 && tty < 4) score *= 0.8;
    }
    
    vector<int> nrx = x;
    vector<int> nry = y;
    for (int i = 0; i < x.size(); ++i)
        if (i > 0 && nrx[i] == -2) nrx[i] = nrx[i - 1];
    for (int i = 0; i < y.size(); ++i)
        if (i > 0 && nry[i] == -2) nry[i] = nry[i - 1];
    
    
    vector<int> nrsx(nrx.begin(), nrx.begin() + time_signature);
    vector<int> nrsy(nry.begin(), nry.begin() + time_signature);
    
    double cr_score0 = contour_rating(nrsx, nrsy);
    
    
    int t = 4 * time_signature;
    if (length_x == 4) t = 2 * time_signature;
    vector<int> bx(x.begin(), x.begin() + t);
    vector<int> by(y.begin(), y.begin() + t);
    double cr_score1 = contour_rating(bx, by);
    vector<int> nrbx(nrx.begin(), nrx.begin() + t);
    vector<int> nrby(nry.begin(), nry.begin() + t);
    double nr_cr_score1 = contour_rating(nrbx, nrby);
    if (nr_cr_score1 > cr_score1) cr_score1 = nr_cr_score1;
    if ((cr_score0 < 0.45  ||  cr_score1 < 0.3) && cr_score0 < 0.6 && cr_score1 < 0.6) return 0.0;
    
    
    if (length_x >= 12) {
        vector<int> hx(x.begin(), x.begin() + time_signature * length_x / 2);
        vector<int> hy(y.begin(), y.begin() + time_signature * length_x / 2);
        vector<int> nrhx(nrx.begin(), nrx.begin() + time_signature * length_x / 2);
        vector<int> nrhy(nry.begin(), nry.begin() + time_signature * length_x / 2);
        if (contour_rating(hx, hy) < 0.5 && contour_rating(nrhx, nrhy) < 0.5) return 0.0;
    }

    double cr_score2 = contour_rating(x, y);
    double nr_cr_score2 = contour_rating(nrx, nry);
    if (nr_cr_score2 > cr_score2) cr_score2 = nr_cr_score2;
    double tr_cr_score3 = (max(cr_score0,  cr_score1) + cr_score2) / 2.0;
    if (length_x >= 10) tr_cr_score3 = (max(cr_score0, cr_score1) * 0.5 + cr_score2) / 1.5;
    if (tr_cr_score3 > cr_score2) cr_score2 = tr_cr_score3;
    return score * cr_score2;
}



vector<int> get_flat_melody(const Section &a) {
    vector<int> mela;
    int lena = (a.end - a.start) * a.time_signature;
    int t1 = 0;
    int i = 0;
    for (int t = 0; t < lena; ++t) {
        if (i < a.melody.size() && t1 + a.melody[i].duration <= t && t < lena) {
            t1 += a.melody[i].duration;
            ++i;
        }
        if (t < lena) {
            mela.push_back(a.melody[i].pitch);
        }
    }
    return mela;
}

vector<int> transpose_melody(vector<int> mel, int delta) {
    vector<int> new_melody(mel);
    for (int i = 0; i< new_melody.size(); ++i)
        if (new_melody[i] > -2) {
            new_melody[i] += delta;
        }
    return new_melody;
}
// Melody similarity score combining rhythm and pitch contour ratings
double cal_melody_score (const Section &a, const Section &b, bool waive_ending = false) {
    vector<int> mela = get_flat_melody(a), melb = get_flat_melody(b);
    
    double r_score = (rhythm_rating(a.melody, b.melody) + rhythm_rating(b.melody, a.melody)) / 2.0;
    double m_score = (melody_dist(mela, melb, a.time_signature, waive_ending) +
                      melody_dist(melb, mela, a.time_signature, waive_ending)) / 2.0;
    int average_a = get_average_melody(mela), average_b = get_average_melody(melb);
    
    if (abs(average_b - average_a) >= 5) {
        int sign = 1;
        if (average_a < average_b) sign = -1;
        vector<int> tmp_melb = transpose_melody(melb, 12 * sign);
        double tmp_mscore = (melody_dist(mela, tmp_melb, a.time_signature, waive_ending) +
                             melody_dist(tmp_melb, mela, a.time_signature, waive_ending)) / 2.0;
        if (tmp_mscore > m_score) m_score = tmp_mscore;
    }
    if (m_score * r_score >= 0.6) return m_score * r_score;
    if (m_score > 0.9) {
        vector<Note> a1 = a.melody, b1 = b.melody;
        a1.insert(a1.begin(), Note(-2, 1));
        b1.insert(b1.begin(), Note(-2, 1));
        double r_score1 = rhythm_rating(a1, b.melody);
        double r_score2 = rhythm_rating(a.melody, b1);
        if (r_score1 * m_score >= 0.6) return r_score1 * m_score;
        if (r_score2 * m_score >= 0.6) return r_score2 * m_score;
    }
    pair<double, double> mcr_scores = get_begin_melody_score(mela, melb, a.time_signature);
    
    if (r_score > 0.85 && m_score > 0.5 &&
        (mcr_scores.first > 0.5 || mcr_scores.second > 0.5) &&
        !(mcr_scores.first < 0.45 || mcr_scores.second < 0.3)) return 0.6;
    return m_score * r_score;
}

// Chord similarity
double cal_chord_score(const Section &a, const Section &b) {
    double chord_score = 0.0;
    int len = min(a.end - a.start, b.end - b.start) * 4;
    int real_len = 0;
    int t1 = 0, t2 = 0;
    int i = 0, j = 0;
    for (int t = 0; t < len; ++t) {
        if (i < a.chords.size() && t1 + a.chords[i].duration <= t) {
            t1 += a.chords[i].duration;
            ++i;
        }
        if (j < b.chords.size() && t2 + b.chords[j].duration <= t) {
            t2 += b.chords[j].duration;
            ++j;
        }
        if (i == a.chords.size() || j == b.chords.size()) break;
        real_len++;
        chord_score += (chord_dist(a.chords[i], b.chords[j]) + chord_dist(b.chords[j], a.chords[i])) / 2.0;
    }
    return chord_score / double(real_len) - double(abs(a.end - a.start - b.end + b.start)) * 0.03;
}

// Judge if two phrases(fragments) are considered repetition or not
bool approximate_matching(const Section &a, const Section &b,
                          bool waive_ending = false) {
    if (abs(a.end - a.start - b.end + b.start) >= 1) return 0; // length
    double chord_score = cal_chord_score(a, b);
    double melody_score = cal_melody_score(a, b, waive_ending);

    
    if (chord_score >= 0.6 && melody_score >= 0.595) return 1;
    if (melody_score > 0.8 && chord_score >= 0.55) return 1;
    if (chord_score > 0.9 && melody_score >= 0.55) return 1;
    if (melody_score >= 0.95) return 1;
    if (a.key_name.size() >= 2) { // modulation in key signature
        Section tmp_b = b;
        for (int k = 1; k <= 11; ++k) {
            tmp_b.transpose_section(1);
            chord_score = cal_chord_score(a, tmp_b);
            melody_score = cal_melody_score(a, tmp_b, waive_ending);
            
            if (chord_score >= 0.6 && melody_score >= 0.595) return 1;
            if (melody_score > 0.8 && chord_score >= 0.55) return 1;
            if (chord_score > 0.9 && melody_score >= 0.55) return 1;
            if (melody_score >= 0.95) return 1;
        }
    }
    return 0;
}

bool include_matches(pair<Section, Section> candidate, vector<pair<Section, Section> > &matches) {
    for (int i = int(matches.size()) - 1; i >= 0; --i) {
        if (candidate.first.start == matches[i].first.start + 1 &&
            candidate.first.end == matches[i].first.end &&
            candidate.second.start == matches[i].second.start + 1 &&
            candidate.second.end == matches[i].second.end &&
            matches[i].first.end == matches[i].second.start)
            return false;
    }
    return true;
}

int clear_outtro(const Section &song) {
    int real_end = 0, mlen = song.melody.size();
    for (int i = 0; i < mlen - 1; ++i)
        real_end += song.melody[i].duration;
    real_end = ((real_end - 1) / song.time_signature) + 1;
    if (real_end > song.end) return song.end;
    return real_end;
}
    
int clear_intro(const Section &song) {
    int real_start = 0, mlen = song.melody.size();
    for (int i = 0; song.melody[i].pitch == -2 && i < mlen - 1; ++i)
        real_start += song.melody[i].duration;
    if ((real_start % (song.time_signature)) >= song.time_signature - 6) real_start = (real_start / song.time_signature) + 1;
    else real_start = (real_start / song.time_signature);
    return real_start;
}


int get_longest_note(vector<Note> melody, bool first_flag = false) {
    int longest = 1;
    int i = 0;
    int current = 0;
    int first = 0;
    while (i < melody.size()) {
        if (melody[i].pitch == -2) current += melody[i].duration;
        else {
            current = melody[i].duration;
            if (first > 1 && first_flag) break;
            first++;
        }
        if (current > longest) longest = current;
        ++i;
    }
    return longest;
}

bool start_boundary_check(const Section &x, const Section &origin) {
    Section start_measure = x.subsection(x.start, x.start + 1);
    if (start_measure.is_bridge(4) || origin.is_subsec_bridge(x.start, x.start + 1) ||
        (start_measure.melody[0].pitch == -2 && start_measure.melody[0].duration >= 10)) return false;
    if (get_longest_note(x.subsection(x.start, x.start + 1).melody, true) < 12) return true;
    int beginning_longest = get_longest_note(x.subsection(x.start, x.start + 2).melody, true);
    int leftmiddle_longest = get_longest_note(x.subsection(x.start + 2, x.end - 1).melody);
    if (x.end - x.start >= 6)
        leftmiddle_longest = get_longest_note(x.subsection(x.start + 2, x.end - 2).melody);

    if (leftmiddle_longest <= 8 || leftmiddle_longest + 4 < beginning_longest) return false;
    return true;
}

// Find all possible repetition phrase pairs
vector<pair<Section, Section> > find_all_match(Section song) {
    int real_end = clear_outtro(song);
    int real_start = clear_intro(song);
    vector<pair<Section, Section> > matches;
    matches.clear();
    bool waive_ending_x, waive_ending_y;
    for (int i = real_start; i < real_end; ++i) {
        if (i >= real_start + 1 && i <= real_start + 3) continue;
        
        for (int d1 = min(real_end - i, 16); d1 >= 4; --d1) {
            Section x = song.subsection(i, i + d1);
            if (!start_boundary_check(x, song) && !x.is_bridge()) continue;
                
            waive_ending_x = false;
            if (i + d1 == real_end || song.subsection(i + d1, i + d1 + 1).is_bridge()) waive_ending_x = true;
            if (!x.is_bridge() && x.contains_bridge()) continue;
            
            for (int j = i + d1; j < real_end; ++j) {
                for (int d2 = real_end - j; d2 >= 4; --d2) {
                    Section y = song.subsection(j, j + d2);
                    if (!start_boundary_check(y, song) && !y.is_bridge()) continue;
                    
                    waive_ending_y = false;
                    if (j + d2 == real_end || song.subsection(j + d2, j + d2 + 1).is_bridge()) waive_ending_y = true;

                    if (!y.is_bridge() && y.contains_bridge()) continue;
                    
                    if (approximate_matching(x, y, (waive_ending_x || waive_ending_y))) {
                        matches.push_back(make_pair(x, y));
                    }
                }
            }
        }
    }
    return matches;
}


/* =====================      Merge Repetition pairs into multiple sets       ====================== */
// merge pairs into no-overlap matches
// this problem is equivalent to find all cliques in an undirected graph

bool appearin(const vector<pair<Section, Section> > &matches, const Section &x, const Section &y) {
    for (int i = 0; i < matches.size(); ++i)
        if ((matches[i].first.is_same(x) && matches[i].second.is_same(y)) || (matches[i].first.is_same(y) && matches[i].second.is_same(x)))
            return 1;
    return 0;
}

int is_add2clique(const Match &oclique, const vector<pair<Section, Section> > &matches, const pair<Section, Section> &edge) {
    int flag1 = 0, flag2 = 0;
    for (int i = 0; i < oclique.sections.size(); ++i) {
        if (edge.first.is_same(oclique.sections[i])) flag1++;
        if (edge.second.is_same(oclique.sections[i])) flag2++;
    }
    if (flag1 + flag2 == 0 || flag1 + flag2 >= 2) return 0;
    Section add(edge.first);
    int return_flag = 1;
    if (flag1 == 1) {add = edge.second; return_flag = 2;}
    
    if (add.start <= oclique.sections.back().start) return 0;
    
    for (int i = 0; i < oclique.sections.size(); ++i)
        if (!oclique.sections[i].non_overlap(add))
            return 0;
    
    for (int i = 0; i < oclique.sections.size(); ++i) {
        if (!appearin(matches, add, oclique.sections[i]))
            return 0;
    }
    return return_flag;
}

int find_pair_index(const Section & a, const Section & b, const vector<pair<Section, Section> > & matches, int match_size) {
    for (int i = 0; i < match_size; ++i)
        if ((matches[i].first.start == a.start && matches[i].first.end == a.end && matches[i].second.start == b.start && matches[i].second.end == b.end) ||
            (matches[i].first.start == b.start && matches[i].first.end == b.end && matches[i].second.start == a.start && matches[i].second.end == a.end))
            return i;
    return -1;
}

bool matches_include(const vector<Match> & finals, const Match & current, bool same = false) {
    int finals_len = finals.size();
    int current_len = current.sections.size();
    for (int i = 0; i < finals_len; ++i) {
        if ((!same && current_len <= finals[i].sections.size()) || (same && current_len == finals[i].sections.size())) {
            int sum = 0, k = 0;
            for (int j = 0; j < current_len && k < finals[i].sections.size(); ++j) {
                for (; k < finals[i].sections.size(); ++k)
                    if (finals[i].sections[k].start == current.sections[j].start &&
                        finals[i].sections[k].end == current.sections[j].end) {
                        ++sum; ++k; break;
                    }
            }
            if (sum == current_len) return true;
        }
    }
    return false;
}

bool cmp_match_size(const Match &a, const Match &b) {
    return a.sections.size() > b.sections.size();
}
vector<Match> merge_matches(const vector<pair<Section, Section> > & matches, bool greedy = false) {
    vector<Match> finals;
    int num = matches.size();
    for (int i = 0; i < num; ++i) {
        vector<Match> candidates;
        Match tmp;
        tmp.sections.push_back(matches[i].first);
        tmp.sections.push_back(matches[i].second);
        tmp.score = 2.0 * cal_chord_score(matches[i].first, matches[i].second) *
          cal_melody_score(matches[i].first, matches[i].second);
        candidates.push_back(tmp);
        for (int j = i + 1; j < num; ++j) {
            int candidate_size = candidates.size();
            if (is_add2clique(candidates[0], matches, matches[j]) >= 1) {
                for (int t = 0; t < candidate_size; ++t) {
                    tmp = candidates[t];
                    int flag = is_add2clique(tmp, matches, matches[j]);
                    if (flag >= 1) {
                        if (flag == 1)
                            tmp.sections.push_back(matches[j].first);
                        else
                            tmp.sections.push_back(matches[j].second);
                        double tscore = 0.0;
                        int n = int(tmp.sections.size()) - 1;
                        for (int k = 0; k < n; ++k) {
                            tscore += cal_chord_score(tmp.sections[k], tmp.sections.back()) *
                                    cal_melody_score(tmp.sections[k], tmp.sections.back());
                        }
                        tmp.score = (double(n - 1) * tmp.score + 2.0 * tscore) / double(n);
                        candidates.push_back(tmp);
                    }
                }
            }
        }
        
        if ((matches[i].first.end - matches[i].first.start) == 4 || (matches[i].first.end - matches[i].first.start) % 8 == 0) {
            for (int j = 0; j < candidates.size(); ++j)
                candidates[j].score += 0.3;
        }
        sort(candidates.begin(), candidates.end(), cmp_match_size);
        vector<Match> to_add;
        bool same_flag = false;
        if (!greedy) same_flag = true;
        for (int t = 0; t < candidates.size(); ++t)
            if (!matches_include(to_add, candidates[t], same_flag))
                to_add.push_back(candidates[t]);
        for (int t = to_add.size() - 1; t >= 0; --t)
            if (!matches_include(finals, to_add[t], same_flag)) {
                finals.push_back(to_add[t]);
            }
      }
    
    return finals;
}



/* =====================      Find the solution cover with best SDL      ====================== */
// Using Dynamic Programming & A* Search

// Add a match set to a cover status
Covermap add_cover(Covermap &a, Match x, double g, double h, int real_start, int real_end) {
    Covermap new_map(a);
    int l = 0;
    int delta_seg = 0;
    unsigned long long am = 1;
    int s, e;
    int section_len = x.sections.size();
    for (int idx = 0; idx < section_len; ++idx) {
        s = x.sections[idx].start;
        e = x.sections[idx].end;
        if (s > real_start && new_map.getmap_at(s - 1) == 0)
            delta_seg++;
        if (e < real_end && new_map.getmap_at(e) == 0)
            delta_seg++;
        
        
        l += e - s;
        if (s < 64) {
            if (e <= 64) new_map.map[0] = new_map.map[0] | (((am << (e - s)) - 1) << s);
            else new_map.map[0] = new_map.map[0] | (((am << (64 - s)) - 1) << s);
            s = 64;
        }
        if (s < 128 && e > 64) {
            if (e <= 128) new_map.map[1] = new_map.map[1] | (((am << (e - s)) - 1) << (s - 64));
            else new_map.map[1] = new_map.map[1] | (((am << (128 - s)) - 1) << (s - 64));
            s = 128;
        }
        if (e > 128) new_map.map[2] = new_map.map[2] | (((am << (e - s)) - 1) << (s - 128));
    }
    new_map.cost = new_map.cost - g * double(l) + g * double(l) / double(x.sections.size()) + h * double(delta_seg);
    new_map.cover = x;
    new_map.from = &a;
    new_map.match_score += x.score;
    return new_map;
}

void map_update(vector<Covermap> &x, Covermap const &y) {
    int flag = 0;
    int xlen = x.size();
    for (int i = 0; i < xlen; ++i) {
        if (x[i].is_same(y)) {
            flag = 1;
            if (x[i].cost > y.cost || (fabs(x[i].cost - y.cost) < 1e-5 && x[i].match_score < y.match_score))
                x[i] = y;
            break;
        }
    }
    if (flag == 0)
        x.push_back(y);
}


int max_covermap_usage = 0;
int sum_covermap_usage = 0;

bool cmp_match(const Match &a, const Match &b) {
    return (a.sections.size() * (a.sections[0].end - a.sections[0].start) > b.sections.size() * (b.sections[0].end - b.sections[0].start) || (a.sections.size() * (a.sections[0].end - a.sections[0].start) == b.sections.size() * (b.sections[0].end - b.sections[0].start) && a.score > b.score));
}
    
bool cmp_maximum_match(const Match &a, const Match &b) {
    return a.score > b.score;
}
    
bool cmp_order_match(const Match &a, const Match &b) {
    return a.sections[0].start < b.sections[0].start;
}
    
bool boundary_cmp(pair<int, double> &a, pair<int, double> &b) {
    return (a.second > b.second + 1e-6 || (a.second > b.second - 1e-6 && a.first < b.first));
}


int song_idx = -1;
string tmp_gt1 = "", tmp_gt2 = "";
bool groundtruth_cmp(string gt, string result);
// Main function for DP + A*
// dp[map][i] = min(dp[map - cover_i][i - 1] + cost_i, dp[map][i - 1])
// dp[map][i] -> dp[map][i + 1], dp[map + cover_i+1][i + 1] + cost_i+1
Covermap dp_max_cover(Section song, vector<Match> match, const vector<Match> & original_match,
                      const vector<pair<Section, Section> > & matches,
                      double g, double h, double tmp_bcost = 1000000000.0, bool add_on = false) {
    int n = match.size();
    vector<Covermap> dp[n + 1];
    dp[0].push_back(Covermap(song.end, g, h, &song));
    clock_t startTime = clock();
    
    int real_start = clear_intro(song);
    int real_end = clear_outtro(song);
    
    if (tmp_bcost > dp[0][0].cost) tmp_bcost = dp[0][0].cost;
    double tolerance = double(real_end - real_start) / 10.0;
        
    max_covermap_usage = 0;
    sum_covermap_usage = 0;
    
    for (int i = 0; i < n; ++i) {
        clock_t currentTime = clock();
        /* IMPORTANT! This is for fast testing: ff the algorithm is running more than 20 minutes, then quit.   */
        /* If you want to test the full algorithm, delete the following 'if' quota/ */
        if ((double)(currentTime - startTime) / CLOCKS_PER_SEC >= 60.0 * 20.0) {
            printf("This version running TOO long, quit at middle!\n");
            dp[0][0].cost = 1000000000.0;
            return dp[0][0];
        }
        
        sum_covermap_usage += dp[i].size();
        if (dp[i].size() > max_covermap_usage) max_covermap_usage = dp[i].size();
        
        if (dp[i].size() == 0) {
            dp[n] = dp[i - 1];
            break;
        }
        dp[i + 1] = dp[i];
        int j = 0, lensize = dp[i + 1].size();
        while (j < lensize) {
            if ((dp[i + 1][j].best_possible_cost(g, h, match[i].sections[0].start, real_end) - tmp_bcost) > tolerance) {
                dp[i + 1].erase(dp[i + 1].begin() + j);
                lensize--;
            }
            else ++j;
        }
        
        for (vector<Covermap>::iterator status = dp[i].begin(); status != dp[i].end(); ++status) {
            if (status->is_ok2add_cover(match[i])) {
                Covermap new_status = add_cover(*status, match[i], g, h, real_start, real_end);
                if ( new_status.cost < tmp_bcost + tolerance ||
                    new_status.best_possible_cost(g, h, match[i].sections[0].start, real_end) < tmp_bcost + tolerance)
                    map_update(dp[i + 1], new_status);
                if (new_status.cost < tmp_bcost)
                    tmp_bcost = new_status.cost;
            }
        }
    }
    
    // merge extra measures and best SDL selection
    int best = 0, final_len = dp[n].size();
    double bcost = 100000000.0;
    vector<pair<int, int> > cover_area;
    vector<double> before_merge_cost;
    double best_before_merge_cost = 100000000.0;
    
    for (int j = 0; j < final_len; ++j) {
        dp[n][j].toString();
        
        dp[n][j].cost = dp[n][j].calculate_cost(g, h, dp[n][j].string_result);
        before_merge_cost.push_back(dp[n][j].cost);
        if (dp[n][j].cost < best_before_merge_cost && dp[n][j].boundary_checking(dp[n][j].string_result))
            best_before_merge_cost = dp[n][j].cost;
        
        dp[n][j].merge_extra(matches, true);
        double alternative_result = dp[n][j].calculate_cost(g, h, dp[n][j].string_result_merge_extra);
        
        dp[n][j].merge_extra(matches, false);
        dp[n][j].cost = dp[n][j].calculate_cost(g, h, dp[n][j].string_result_merge_extra);
        
        if (alternative_result + 1e-5 < dp[n][j].cost) {
            dp[n][j].merge_extra(matches, true);
            dp[n][j].cost = alternative_result;
        }
        
        cover_area.push_back(make_pair(dp[n][j].calculate_cover_area(dp[n][j].string_result_merge_extra),  dp[n][j].calculate_cover_area(dp[n][j].string_result)));
        
        if (dp[n][j].cost < bcost && dp[n][j].boundary_checking(dp[n][j].string_result_merge_extra)) {
            bcost = dp[n][j].cost; best = j;
        }
        
    }
   
    
    tolerance = double(real_end - real_start) / 15.0;
    double tolerance_bcost = bcost;
        
        
    vector<int> candidates;
    candidates.clear();
    for (int j = 0; j < final_len; ++j)
        if (dp[n][j].boundary_checking(dp[n][j].string_result_merge_extra) &&
            (before_merge_cost[j] - best_before_merge_cost < tolerance ||
            (before_merge_cost[j] - best_before_merge_cost < tolerance * 2.2 && dp[n][j].cost - tolerance_bcost < tolerance))) {
            bool add_flag = true;
            for (int t = 0; t < candidates.size(); ++t) {
                if (dp[n][j].string_result_merge_extra == dp[n][candidates[t]].string_result_merge_extra) {
                    add_flag = false;
                    if (before_merge_cost[j] + 1e-5 < before_merge_cost[candidates[t]] ||
                        (fabs(before_merge_cost[j] - before_merge_cost[candidates[t]]) < 1e-5 &&
                        cover_area[j].second > cover_area[candidates[t]].second) ||
                        (fabs(before_merge_cost[j] - before_merge_cost[candidates[t]]) < 1e-5 &&
                            cover_area[j].second == cover_area[candidates[t]].second &&
                         dp[n][j].match_score > dp[n][candidates[t]].match_score))
                        candidates[t] = j;
                    break;
                }
            }
            if (add_flag)
                candidates.push_back(j);
        }
    
    if (candidates.size() == 0) return dp[n][0];
    
    pair<int, int> best_cover = make_pair(0, 0);
    for (int t = 0; t < candidates.size(); ++t) {
        int j = candidates[t];
        if (cover_area[j].first > best_cover.first) best_cover.first = cover_area[j].first;
        if (cover_area[j].second > best_cover.second) best_cover.second = cover_area[j].second;
    }
    for (int t = 0; t < candidates.size(); ++t) {
        int j = candidates[t];
        int l0 = dp[n][j].string_result.length(), l1 = dp[n][j].string_result_merge_extra.length();
        if (best_cover.first > cover_area[j].first &&
            (dp[n][j].string_result_merge_extra[l1 - 2] == 'X' ||
            (dp[n][j].string_result_merge_extra[l1 - 2] == 'o' && dp[n][j].string_result_merge_extra[l1 - 4] == 'X')))
            cover_area[j].first++;
        if (best_cover.second > cover_area[j].second &&
            (dp[n][j].string_result[l0 - 2] == 'X' ||
            (dp[n][j].string_result[l0 - 2] == 'o' && dp[n][j].string_result[l0 - 4] == 'X')))
            cover_area[j].second++;
    }
    
        
    // if the both before merge and after merge cost are the smallest
    best = -1;
    bcost = 100000000.0;
    for (int t = 0; t < candidates.size(); ++t) {
        int j = candidates[t];
        double lenvar = dp[n][j].length_variance(dp[n][j].string_result_merge_extra);
        double cover_score = 0.5 * double(best_cover.first - cover_area[j].first) +
                             0.1 * double(best_cover.second - cover_area[j].second);
        if (dp[n][j].cost + before_merge_cost[j] + lenvar + cover_score < bcost)
            bcost = dp[n][j].cost + before_merge_cost[j] + lenvar + cover_score;
    }
    
    for (int t = 0; t < candidates.size(); ++t) {
        int j = candidates[t];
        double lenvar = dp[n][j].length_variance(dp[n][j].string_result_merge_extra);
        double cover_score = double (best_cover.first - cover_area[j].first + best_cover.second - cover_area[j].second) / 8.0;
        if (fabs(before_merge_cost[j] - best_before_merge_cost) < 1e-5 &&
            fabs(dp[n][j].cost - tolerance_bcost) < 1e-5 &&
            fabs(dp[n][j].cost + before_merge_cost[j] + lenvar + cover_score - bcost) < 1e-5) {
            if (best == -1 || dp[n][j].match_score > dp[n][best].match_score)
                best = j;
        }
    }
    if (best != -1) {
        if (!add_on) {
            dp[n][best].small_extra_merge();
            return dp[n][best];
        }
    } else {
        // find the best before + after merge cost + lenvar with valid regularity
        best = -1;
        bcost = 100000000.0;
        for (int t = 0; t < candidates.size(); ++t) {
            int j = candidates[t];
            double lenvar = dp[n][j].length_variance(dp[n][j].string_result_merge_extra);
            double cover_score = 0.5 * double(best_cover.first - cover_area[j].first) +
                                 0.1 * double(best_cover.second - cover_area[j].second);
            double cur = dp[n][j].cost + 0.95 * before_merge_cost[j] + lenvar + cover_score;
            if (cur < bcost ||
                    (fabs(cur - bcost) < 1e-5 && dp[n][j].match_score > dp[n][best].match_score) ||
                    ((fabs(cur - bcost) < 1e-5 && fabs(dp[n][j].match_score - dp[n][best].match_score) < 1e-5) &&
                     ((cover_area[j].first > cover_area[best].first && cover_area[j].second + 2 >= cover_area[best].second) ||
                      (cover_area[j].first == cover_area[best].first && cover_area[j].second > cover_area[best].second) ||
                      (cover_area[j].first == cover_area[best].first && cover_area[j].second == cover_area[best].second &&
                       before_merge_cost[j] < before_merge_cost[best]))))
            {best = j; bcost = cur;}
        }
        
        if (!add_on) {
            dp[n][best].small_extra_merge();
            return dp[n][best];
        }
    }

    vector<Match> tmp_original_match = original_match;
    sort(tmp_original_match.begin(), tmp_original_match.end(), cmp_match);
    Covermap best_new_status = dp[n][best];
    for (vector<Match>::iterator mj = tmp_original_match.begin(); mj !=  tmp_original_match.end(); ++mj) {
        if (dp[n][best].is_ok2add_cover(*mj)) {
            Covermap new_status = add_cover(dp[n][best], *mj, g, h, real_start, real_end);
            new_status.toString();
            new_status.merge_extra(matches);
            new_status.cost = new_status.calculate_cost(g, h, new_status.string_result_merge_extra);
            if (new_status.cost + 1e-6 < best_new_status.cost)
                best_new_status = new_status;
        }
    }
    best_new_status.small_extra_merge();
    return best_new_status;
}


/* =====================     Output: compare results to the ground truth       ====================== */

bool groundtruth_cmp(string gt, string result) {
    if (gt == result) return true;
    // consider outro number difference tolarence at -1, or -2
    int outtro_pos = result.length() - 1;
    while (outtro_pos >= 0 && result[outtro_pos] >= '0' && result[outtro_pos] <= '9') outtro_pos--;
    int num = 0;
    for (int i = outtro_pos + 1; i < result.length(); ++i)
        num = num * 10 + result[i] - '0';
    string new_result = result.substr(0, outtro_pos);
    num--;
    if (num > 0) {
        new_result += result[outtro_pos] + to_string(num);
    }
    if (gt == new_result) return true;
    return false;
}

void write_result(string result, string dir_path) {
    FILE *fout;
    fout = fopen((dir_path + "result.txt").c_str(), "a+");
    fprintf(fout, "%s\n", result.c_str());
    printf("%s\n", result.c_str());
    fclose(fout);
}
    


/* =====================      MAIN PROGRAM       ====================== */

int main(int argc, char *argv[]) {
    
    // data path
    string dir_path = "POP909/";

    // input id of the song
    if (argc != 2) {
        printf("please enter an id!");
        return 0;
    }
    int idx = atoi(argv[1]);
    if (idx <= 0 || idx > 1000) {
        printf("id out of range!");
        return 0;
    }

    
    
    song_idx = idx;
    
    vector<int> time_signature_inThree = {34, 62, 102, 107, 152, 173, 176, 203, 215, 231, 254, 280, 307, 328, 369, 584, 592, 653, 654, 662, 744, 749, 756, 770, 799, 843, 869, 872, 887};
    
    // load data
    FILE *inm, *inc, *ink;
    string name_idx = to_string(idx);
    if (name_idx.size() == 1) name_idx = "00" + name_idx;
    else if (name_idx.size() == 2) name_idx = "0" + name_idx;
    inm = fopen((dir_path + name_idx + "/melody.txt").c_str(), "r");
    inc = fopen((dir_path + name_idx + "/finalized_chord.txt").c_str(), "r");
    ink = fopen((dir_path + name_idx + "/analyzed_key.txt").c_str(), "r");
    
    Section song;
    song.start = 0;
    int length = 0;
    // input chords
    char cname[10], tmp_s;
    while (fscanf(inc, "%s", cname) != EOF) {
        do {fscanf(inc, "%c", &tmp_s);} while (tmp_s != '[');
        vector<int> chord_tones;
        int tc, bass, tl;
        do {
            fscanf(inc, "%d", &tc);
            chord_tones.push_back(tc);
            fscanf(inc, "%c", &tmp_s);
        } while(tmp_s != ']');
        fscanf(inc, "%d %d\n", &bass, &tl);
        Chord tmp_chord(cname, bass, tl, chord_tones);
        song.chords.push_back(tmp_chord);
        length += tl;
    }
    
    // input time signature
    song.time_signature = 16;
    song.end = length / 4 + 1;
    if (find(time_signature_inThree.begin(), time_signature_inThree.end(), idx) != time_signature_inThree.end() ) {
        song.time_signature = 12;
        song.end = length / 3 + 1;
    }
    
    // input melody
    int a, b;
    int melody_length = 0;
    while (fscanf(inm, "%d %d\n", &a, &b) != EOF) {
        if (a == 0) a = -2;
        song.melody.push_back(Note(a, b));
        melody_length += b;
    }
    song.melody.push_back(Note(-2, 1000));
    melody_length = (melody_length - 1) / song.time_signature + 1;
    if (melody_length > song.end) song.end = melody_length;
    
    // input key signature
    char tmp_key[200];
    while (fscanf(ink, "%s", tmp_key) != EOF) {
        song.key_name.push_back(tmp_key);
    }
    
    
    // control param for SDL
    double g = 1.3, h = 1.0;
    
    // ground truth & output file
    FILE *out, *outseg, *gt1, *gt2;
    out = fopen((dir_path + name_idx + "/phrases_log.txt").c_str(), "w");
    outseg = fopen((dir_path + name_idx + "/phrases.txt").c_str(), "w");
    gt1 = fopen((dir_path + name_idx + "/human_label1.txt").c_str(), "r");
    gt2 = fopen((dir_path + name_idx + "/human_label2.txt").c_str(), "r");
    
    
    char groundtruth1[100], groundtruth2[100];
    fscanf(gt1, "%s", groundtruth1);
    fscanf(gt2, "%s", groundtruth2);
    tmp_gt1 = groundtruth1;
    tmp_gt2 = groundtruth2;
        
    // matching
    int real_end = clear_outtro(song);
    int real_start = clear_intro(song);
    int real_len = real_end - real_start;
    fprintf(out, "song %s, real len: %d\n",  name_idx.c_str(), real_len);

    
    clock_t startTime, endTime;
    startTime = clock();
    //find all possible repetition pairs
    vector<pair<Section, Section> > matches = find_all_match(song);
    if (matches.size() == 0) {
        fprintf(out, "no matches found!");
        string temp_result = "";
        if (real_start > 0) temp_result += "i" + to_string(real_start);
        temp_result += "X" + to_string(real_len);
        if (real_end < song.end) temp_result += "o" + to_string(song.end - real_end);
        fprintf(outseg, "%s\n", temp_result.c_str());
        fprintf(out, "%s\n", temp_result.c_str());
        
        if (groundtruth_cmp(groundtruth1, temp_result) || groundtruth_cmp(groundtruth2, temp_result))
            write_result(name_idx + " : " + temp_result + ", Correct!", "./");
        else
            write_result(name_idx + " : " + temp_result + ", Incorrect! Ground Truth: " + string(groundtruth1) + ", " + string(groundtruth2), "./");
        return 0;
    }
    
    /* IMPORTANT! this is an approximation for fast testing: when the matches are too much, reduce them */
    /* If you want to run the full version, delete the followng 'if' quota */
    if (real_len >= 120 && matches.size() >= 2000) {
        vector<pair<Section, Section> > matches_new;
        matches_new.clear();
        for (int k = 0; k < matches.size(); ++k) {
            if ((matches[k].first.end - matches[k].first.start) % 8 == 0)
                matches_new.push_back(matches[k]);
        }
        matches = matches_new;
    }
    
    // merge repetition pairs into matching sets
    vector<Match> final_match_greedy = merge_matches(matches, true);
    
    int greedy_size = int(final_match_greedy.size());
    fprintf(out, "num pairs %lu, greedy matches %d\n", matches.size(), greedy_size);
        
    int percent = 20;
    if (greedy_size >= 600 || real_len >= 80) percent = 10;
           
    // Approximation version 1: only use the top 20% or 10% of the match sets by matching score
    vector<Match> final_match_maximum;
    int last_temp_size = 0;
    for (int tcount = 0; tcount < 20; ++tcount) {
        int temp_size = max(int(greedy_size * (tcount + 1) / 20), last_temp_size + 1);
        if (temp_size > greedy_size) temp_size = greedy_size;
        if (temp_size > last_temp_size) {
            vector<Match> temp(final_match_greedy.begin() + last_temp_size, final_match_greedy.begin() + temp_size);
            sort(temp.begin(), temp.end(), cmp_maximum_match);
            final_match_maximum.insert(final_match_maximum.end(), temp.begin(), temp.begin() + int(greedy_size * percent / 2000) + 1);
            last_temp_size = temp_size;
        }
    }
    sort(final_match_maximum.begin(), final_match_maximum.end(), cmp_order_match);
    Covermap *maximum_result = new Covermap(dp_max_cover(song, final_match_maximum, final_match_greedy, matches,
                                                         g, h, 1000000.0, true));
    fprintf(out, "MAXIMUM %d percent: %s cost %.2lf match_score %.2lf\n", percent, maximum_result->string_result_merge_extra.c_str(), maximum_result->cost, maximum_result->match_score);
        
    
    // Approximation version 2: only use the top 20% or 10% of the match sets by covering length
    vector<Match> final_match_appro;
    last_temp_size = 0;
    for (int tcount = 0; tcount < 20; ++tcount) {
        int temp_size = max(int(greedy_size * (tcount + 1) / 20), last_temp_size + 1);
        if (temp_size > greedy_size) temp_size = greedy_size;
        if (temp_size > last_temp_size) {
            vector<Match> temp(final_match_greedy.begin() + last_temp_size, final_match_greedy.begin() + temp_size);
            sort(temp.begin(), temp.end(), cmp_match);
            final_match_appro.insert(final_match_appro.end(), temp.begin(), temp.begin() + int(greedy_size * percent / 2000) + 1);
            last_temp_size = temp_size;
        }
    }
    sort(final_match_appro.begin(), final_match_appro.end(), cmp_order_match);
    Covermap *appro_result = new Covermap(dp_max_cover(song, final_match_appro,final_match_greedy,  matches,
                                                       g, h, 1000000.0, true));
    fprintf(out, "APPROX  %d percent: %s cost %.2lf match_score %.2lf\n", percent, appro_result->string_result_merge_extra.c_str(), appro_result->cost, appro_result->match_score);
    
    
    // Approximation version 3: use the combination of partial match sets in approximation version 1 & 2
    vector<Match> final_match_mix;
    final_match_mix.insert(final_match_mix.end(), final_match_maximum.begin(), final_match_maximum.end());
    final_match_mix.insert(final_match_mix.end(), final_match_appro.begin(), final_match_appro.end());
    sort(final_match_mix.begin(), final_match_mix.end(), cmp_order_match);
    int j = 1, lensize = final_match_mix.size();
    while (j < lensize) {
        if (final_match_mix[j].is_same(final_match_mix[j - 1]) ) {
            final_match_mix.erase(final_match_mix.begin() + j);
            lensize--;
        }
        else ++j;
    }
    Covermap *mix_result = new Covermap(dp_max_cover(song, final_match_mix, final_match_greedy, matches,
                                                     g, h, 1000000.0, true));
    fprintf(out, "MIX-MA  %d percent: %s cost %.2lf match_score %.2lf\n", percent, mix_result->string_result_merge_extra.c_str(), mix_result->cost, mix_result->match_score);

    
    // Approximation version 4: randomly use 10% of the match sets
    int random_num = 20;
    if (greedy_size >= 600 || real_len >= 80) random_num = 10;
    //if (greedy_size >= 1500 || real_len >= 120) random_num = 5;
    Covermap *random_result = NULL;
    for (int j = 0; j < random_num; ++j) {
        unsigned seed = chrono::system_clock::now().time_since_epoch().count();
        auto gen = std::default_random_engine(seed);
        if (greedy_size > 0) shuffle(final_match_greedy.begin(), final_match_greedy.end(), gen);
        vector<Match> final_match_random(final_match_greedy.begin(), final_match_greedy.begin() + int(greedy_size /* * (double(0.5) * (j / (random_num / 2) + 2))*/ / 10) + 1);
        if (greedy_size > 0) sort(final_match_random.begin(), final_match_random.end(), cmp_order_match);
        Covermap *tmp_random_result = new Covermap(dp_max_cover(song, final_match_random, final_match_greedy, matches,
                                                                g, h, 1000000.0, true));
        if (random_result == NULL ||
            random_result->cost > tmp_random_result->cost ||
            (random_result->cost > tmp_random_result->cost - 1e-6 && random_result->match_score < tmp_random_result->match_score))
            random_result = tmp_random_result;
    }
    fprintf(out, "RANDOM %d percent: %s cost %.2lf match_score %.2lf\n", 10, random_result->string_result_merge_extra.c_str(), random_result->cost, random_result->match_score);
    endTime = clock();
    double runTime = (double)(endTime - startTime) / CLOCKS_PER_SEC;
    fprintf(out, "Four approximations time used in total: %.2lf\n", runTime);
        
    
    // Approximation version 5: reducing the match sets by deleting invalid boundary matches
    //                          according to previous approximations
    vector<int> boundaries;
    boundaries.push_back(song.start);
    for (int k = song.start + 1; k < song.end; ++k) {
        if (appro_result->is_boundary(k) && maximum_result->is_boundary(k) && random_result->is_boundary(k))
            boundaries.push_back(k);
    }
    boundaries.push_back(song.end);
    for (int k = 0; k < boundaries.size() - 1; ++k) {
        fprintf(out, "[%d, %d] ", boundaries[k], boundaries[k + 1]);
    }
    fprintf(out, "\n");
    // delete incorrect matches according to boundaries
    int bflag = 0;
    j = 0;
    lensize = int(matches.size());
    fprintf(out, "original matches: %d ", lensize);
    while (j < lensize) {
        bflag = 0;
        for (int k = 1; k < boundaries.size() - 1; ++k)
            if ((matches[j].first.start < boundaries[k] && matches[j].first.end > boundaries[k]) ||
                (matches[j].second.start < boundaries[k] && matches[j].second.end > boundaries[k])) {
                matches.erase(matches.begin() + j);
                lensize--;
                bflag = 1;
                break;
            }
        if (bflag == 0) ++j;
        }
    fprintf(out, "after deletion matches: %d \n", lensize);
    //vector<Match> final_match_greedy_after_cut = merge_matches(matches, true);
    
    // pick up the best one among all approximation versions
    Covermap *best_approach = maximum_result;
    if (mix_result->cost < best_approach->cost + 2.0)
        best_approach = mix_result;
    if (appro_result->cost + 5.0 < best_approach->cost)
        best_approach = appro_result;
    if (random_result->cost + 3.0 < best_approach->cost)
        best_approach = random_result;
    
    
    // FULL version: structure segment analysis => dynamic programming + A*, set g & h
    if (greedy_size > 0) sort(final_match_greedy.begin(), final_match_greedy.end(), cmp_order_match);
    //if (greedy_size > 0) sort(final_match_greedy_after_cut.begin(), final_match_greedy_after_cut.end(), cmp_order_match);
    
    Covermap* result = new Covermap(dp_max_cover(song, final_match_greedy, final_match_greedy,
                                                 matches, g, h, best_approach->cost + 10.0));
    if (result->cost < 1000000000.0) {
        fprintf(out, "FINAL : ");
        best_approach = result;
    }
    else fprintf(out, "Use approximation : ");
    
    fprintf(outseg, "%s\ncost %.2lf match_score %.2lf\n",
           best_approach->string_result_merge_extra.c_str(), best_approach->cost, best_approach->match_score);
    fprintf(out, "%s cost %.2lf match_score %.2lf\n\n", best_approach->string_result_merge_extra.c_str(), best_approach->cost, best_approach->match_score);
            
    if (groundtruth_cmp(groundtruth1, best_approach->string_result) ||
        groundtruth_cmp(groundtruth1, best_approach->string_result_merge_extra) ||
        groundtruth_cmp(groundtruth2, best_approach->string_result) ||
        groundtruth_cmp(groundtruth2, best_approach->string_result_merge_extra))
        write_result(name_idx + " : " + best_approach->string_result_merge_extra + ", Correct!", "./");
    else
        write_result(name_idx + " : " + best_approach->string_result_merge_extra + ", Incorrect! Ground Truth: " + string(groundtruth1) + ", " + string(groundtruth2), "./");
        
    
    fclose(outseg);
    
    return 0;
}
