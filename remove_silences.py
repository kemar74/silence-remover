import moviepy
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.editor import concatenate_videoclips

import math

file = "HeuristicEvaluation - HARTLEY Marc.mp4"


def find_silences(audiofile, silence_duration = None, epsilon = 0.05, subset_size = 200, verbose = False):
    fps = audiofile.fps
    silences = []
    last_silence_time = None
    current_subset = 0

    corrected_i = 0

    for i, current_frame in enumerate(audiofile.iter_frames()):
        current_subset = int((i / fps) / subset_size)
        frame = current_frame[0]
        corrected_i = i - current_subset * subset_size
        if i % (audiofile.duration * fps // 10) == 0:
            if verbose:
                print(f"{round(100 * i / (audiofile.duration * fps))}%")
        if abs(frame) <= epsilon:
            if last_silence_time == i - 1:
                if silences[-1][3] < current_subset:
                    silences[-1] = (0, 0, 0, 0)#(silences[-1][0], (i - (current_subset - 1) * subset_size - 1) - silences[-1][3] * subset_size, (corrected_i-1) - silences[-1][0], silences[-1][3]) # start, end, duration, subset
                    silences.append((corrected_i, 0, 0, current_subset))
                last_silence_time = i

            else:
                silences.append((corrected_i, 0, 0, current_subset))
                last_silence_time = i

        else:
            silences[-1] = (silences[-1][0], corrected_i, (corrected_i - 1) - silences[-1][0], silences[-1][3]) # start, end, duration, subset

    if len(silences[-1]) == 1:
        silences[-1] = (silences[-1][0], (corrected_i -1), (corrected_i -1) - silences[-1][0], silences[-1][3])

    if silence_duration is not None:
        silences = [silence for silence in silences if silence[2] >= silence_duration * fps]
    return silences

def remove_silences(file, output_name = "silences_removed.mp4", min_silence_duration = 0.5, keep_silence_percent = 0.2, keep_specific_duration = False, verbose = True):
    name_splited = output_name.split(".")
    filename = ".".join(name_splited[:-1])
    if len(name_splited) > 1:
        ext = name_splited[-1]
    else:
        ext = ".mp4"
        
    subset_size = 200000
    epsilon = 0.05

    audio = AudioFileClip(file)

    original_videos = []
    videos = []
    for i in range(math.ceil(audio.duration / subset_size)):
        video = VideoFileClip(file)
        video = video.subclip(i * subset_size, min(video.duration, (i+1) * subset_size))
        videos.append(video)
        original_videos.append(video.copy())

    silences = find_silences(audio, silence_duration = min_silence_duration, subset_size =  subset_size, verbose = verbose)
    if keep_specific_duration:
        silences.sort(key = lambda x: x[2], reverse = True)

    for i in range(len(silences)):
        i_start = silences[i][0]
        i_end = silences[i][1]
        i_current_duration = i_end - i_start
        i_start += i_current_duration * keep_silence_percent/2
        i_end   -= i_current_duration * keep_silence_percent/2
        i_cut_duration = i_end - i_start

        for j in range(i + 1, len(silences)):
            if silences[i][0] < silences[j][0]:
                if silences[i][3] == silences[j][3]:
                    silences[j] = (silences[j][0] - i_cut_duration, silences[j][1] - i_cut_duration, silences[j][2], silences[j][3])

    if verbose:
        print(len(silences), "silences found")

    total_duration = 0
    for silence in silences:
        total_duration = 0
        for video in videos:
            total_duration += video.duration
        start = silence[0] / audio.fps
        end = silence[1] / audio.fps
        current_duration = end - start
        start += current_duration * keep_silence_percent/2
        end   -= current_duration * keep_silence_percent/2
        if verbose:
            print("-> from ", round(start, 2), "to", round(end, 2), "of video", silence[3])
        try:
            videos[silence[3]] = videos[silence[3]].cutout(start - silence[3] * subset_size, end - silence[3] * subset_size)
        except:
            print("Ignored")
        print("current duration :", total_duration)



        if keep_specific_duration and total_duration <= keep_specific_duration:
            break

    if keep_specific_duration and total_duration > keep_specific_duration and verbose:
        print(f"We didn't find enough silence to short the video to {keep_specific_duration}s, the video is {total_duration}s long")

    for i, video in enumerate(videos):
        video.write_videofile(filename + "_part_" + str(i+1) + "." + ext)

    final_clip = concatenate_videoclips(videos)
    final_clip.write_videofile(filename + "." + ext)


remove_silences(file, min_silence_duration = 0.5, keep_specific_duration = 15 * 60)