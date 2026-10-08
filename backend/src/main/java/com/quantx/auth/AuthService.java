package com.quantx.auth;

import com.quantx.auth.dto.LoginRequest;
import com.quantx.auth.dto.LoginResponse;
import com.quantx.common.ApiException;
import com.quantx.common.ErrorCode;
import com.quantx.user.User;
import com.quantx.user.UserRepository;
import com.quantx.user.UserScopeRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final UserScopeRepository userScopeRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtProvider jwtProvider;

    @Transactional(readOnly = true)
    public LoginResponse login(LoginRequest req) {
        User user = userRepository.findByUserId(req.userId())
                .orElseThrow(() -> new ApiException(ErrorCode.UNAUTHORIZED, "사용자 없음"));

        if (!user.isActive()) {
            throw new ApiException(ErrorCode.UNAUTHORIZED, "비활성 사용자");
        }

        if (!passwordEncoder.matches(req.password(), user.getPasswordHash())) {
            throw new ApiException(ErrorCode.UNAUTHORIZED, "비밀번호 불일치");
        }

        List<String> scopes = userScopeRepository.findByUserId(user.getId()).stream()
                .map(s -> s.getScope())
                .toList();

        String token = jwtProvider.createAccessToken(
                user.getUserId(), user.getName(), user.getRole().name(), scopes);

        return new LoginResponse(
                token,
                new LoginResponse.UserInfo(user.getUserId(), user.getName(), user.getRole().name(), scopes)
        );
    }
}